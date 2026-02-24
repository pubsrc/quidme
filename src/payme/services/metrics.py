"""Prometheus metrics for Payme API."""

from __future__ import annotations

import logging
from collections.abc import Callable

from boto3.dynamodb.conditions import Attr
from prometheus_client import Counter, Gauge

from payme.core.settings import settings
from payme.db.dynamodb import get_dynamodb_resource

logger = logging.getLogger(__name__)


def _scan_count(table_name: str, filter_expression=None) -> int:
    table = get_dynamodb_resource().Table(table_name)
    total = 0
    scan_kwargs: dict = {"Select": "COUNT"}
    if filter_expression is not None:
        scan_kwargs["FilterExpression"] = filter_expression

    response = table.scan(**scan_kwargs)
    total += int(response.get("Count", 0))
    last_evaluated_key = response.get("LastEvaluatedKey")
    while last_evaluated_key:
        response = table.scan(ExclusiveStartKey=last_evaluated_key, **scan_kwargs)
        total += int(response.get("Count", 0))
        last_evaluated_key = response.get("LastEvaluatedKey")
    return total


def _safe_count(get_count: Callable[[], int], metric_name: str) -> float:
    try:
        return float(get_count())
    except Exception:
        logger.exception("Failed to compute metric %s", metric_name)
        return 0.0


def _count_users() -> int:
    return _scan_count(settings.ddb_table_users)


def _count_verified_accounts() -> int:
    return _scan_count(
        settings.ddb_table_stripe_accounts,
        filter_expression=Attr("status").eq("VERIFIED"),
    )


def _count_payment_links() -> int:
    return _scan_count(settings.ddb_table_payment_links)


def _count_transactions() -> int:
    return _scan_count(settings.ddb_table_transactions)


USERS_TOTAL = Gauge(
    "payme_users_total",
    "Total number of users.",
)
USERS_TOTAL.set_function(lambda: _safe_count(_count_users, "payme_users_total"))

VERIFIED_ACCOUNTS_TOTAL = Gauge(
    "payme_verified_accounts_total",
    "Total number of verified connected accounts.",
)
VERIFIED_ACCOUNTS_TOTAL.set_function(
    lambda: _safe_count(_count_verified_accounts, "payme_verified_accounts_total")
)

PAYMENT_LINKS_TOTAL = Gauge(
    "payme_payment_links_total",
    "Total number of payment links.",
)
PAYMENT_LINKS_TOTAL.set_function(
    lambda: _safe_count(_count_payment_links, "payme_payment_links_total")
)

TRANSACTIONS_TOTAL = Gauge(
    "payme_transactions_total",
    "Total number of transactions.",
)
TRANSACTIONS_TOTAL.set_function(
    lambda: _safe_count(_count_transactions, "payme_transactions_total")
)

TRANSFERS_SUCCESSFUL_TOTAL = Counter(
    "payme_transfers_successful_total",
    "Count of successful transfer attempts to connected accounts.",
)

TRANSFERS_FAILED_TOTAL = Counter(
    "payme_transfers_failed_total",
    "Count of failed transfer attempts to connected accounts.",
)

PAYOUTS_SUCCESSFUL_TOTAL = Counter(
    "payme_payouts_successful_total",
    "Count of successful payout creations.",
)

PAYOUTS_FAILED_TOTAL = Counter(
    "payme_payouts_failed_total",
    "Count of failed payout creations.",
)


def observe_transfer_result(*, successful: int = 0, failed: int = 0) -> None:
    if successful > 0:
        TRANSFERS_SUCCESSFUL_TOTAL.inc(successful)
    if failed > 0:
        TRANSFERS_FAILED_TOTAL.inc(failed)


def observe_payout_result(*, successful: int = 0, failed: int = 0) -> None:
    if successful > 0:
        PAYOUTS_SUCCESSFUL_TOTAL.inc(successful)
    if failed > 0:
        PAYOUTS_FAILED_TOTAL.inc(failed)
