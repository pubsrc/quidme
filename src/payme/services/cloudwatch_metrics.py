"""CloudWatch custom metrics helpers (low-cardinality, cost-conscious)."""

from __future__ import annotations

import logging
import os
from typing import Any

import boto3

from payme.core.settings import settings

logger = logging.getLogger(__name__)

_NAMESPACE = "Payme/API"
_cloudwatch_client: Any | None = None
_disabled = False

# Keep this to 8 metrics so a single account/region stays within the free custom-metric tier.
METRIC_USERS = "Users"
METRIC_VERIFIED_ACCOUNTS = "VerifiedAccounts"
METRIC_PAYMENT_LINKS = "PaymentLinks"
METRIC_TRANSACTIONS = "Transactions"
METRIC_SUCCESSFUL_TRANSFERS = "SuccessfulTransfers"
METRIC_FAILED_TRANSFERS = "FailedTransfers"
METRIC_SUCCESSFUL_PAYOUTS = "SuccessfulPayouts"
METRIC_FAILED_PAYOUTS = "FailedPayouts"


def _should_skip() -> bool:
    # Avoid noisy/slow network calls during tests.
    return "PYTEST_CURRENT_TEST" in os.environ


def _client():
    global _cloudwatch_client
    if _cloudwatch_client is None:
        _cloudwatch_client = boto3.client("cloudwatch", region_name=settings.cognito_region)
    return _cloudwatch_client


def _put_metric_data(metric_data: list[dict[str, Any]]) -> None:
    global _disabled
    if _disabled or _should_skip():
        return
    try:
        _client().put_metric_data(
            Namespace=_NAMESPACE,
            MetricData=metric_data,
        )
    except Exception:
        # Keep business flow unaffected; disable further attempts in this process.
        _disabled = True
        logger.exception("CloudWatch metric publish failed; disabling metrics publishing for this runtime")


def increment_metric(metric_name: str, value: int = 1) -> None:
    if value <= 0:
        return
    _put_metric_data(
        [
            {
                "MetricName": metric_name,
                "Unit": "Count",
                "Value": float(value),
            }
        ]
    )


def increment_users(count: int = 1) -> None:
    increment_metric(METRIC_USERS, count)


def increment_verified_accounts(count: int = 1) -> None:
    increment_metric(METRIC_VERIFIED_ACCOUNTS, count)


def increment_payment_links(count: int = 1) -> None:
    increment_metric(METRIC_PAYMENT_LINKS, count)


def increment_transactions(count: int = 1) -> None:
    increment_metric(METRIC_TRANSACTIONS, count)


def record_transfer_results(*, successful: int = 0, failed: int = 0) -> None:
    metric_data: list[dict[str, Any]] = []
    if successful > 0:
        metric_data.append({"MetricName": METRIC_SUCCESSFUL_TRANSFERS, "Unit": "Count", "Value": float(successful)})
    if failed > 0:
        metric_data.append({"MetricName": METRIC_FAILED_TRANSFERS, "Unit": "Count", "Value": float(failed)})
    if metric_data:
        _put_metric_data(metric_data)


def record_payout_results(*, successful: int = 0, failed: int = 0) -> None:
    metric_data: list[dict[str, Any]] = []
    if successful > 0:
        metric_data.append({"MetricName": METRIC_SUCCESSFUL_PAYOUTS, "Unit": "Count", "Value": float(successful)})
    if failed > 0:
        metric_data.append({"MetricName": METRIC_FAILED_PAYOUTS, "Unit": "Count", "Value": float(failed)})
    if metric_data:
        _put_metric_data(metric_data)
