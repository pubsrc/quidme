"""
Stripe webhook handling: verify payload and route events.

Payment-link payment events are delegated to stripe_event_handler.
Account lifecycle (account.updated) is handled here.
"""

from __future__ import annotations

import logging
from typing import Any

import stripe

from payme.core.constants import StripeAccountStatus
from payme.db.repositories import StripeAccountRepository
from payme.services.stripe_event_handler import (
    handle_checkout_session_completed,
    handle_invoice_paid,
    handle_payment_failed,
    handle_payment_succeeded,
    handle_subscription_created,
)

logger = logging.getLogger(__name__)

PAYMENT_SUCCEEDED_EVENTS = {"payment_intent.succeeded"}
PAYMENT_FAILED_EVENTS = {"payment_intent.payment_failed"}
INVOICE_PAID_EVENTS = {"invoice.paid"}
SUBSCRIPTION_CREATED_EVENT = "customer.subscription.created"
CHECKOUT_SESSION_COMPLETED_EVENT = "checkout.session.completed"
ACCOUNT_UPDATED_EVENT = "account.updated"


def _to_dict(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "get"):
        return dict(obj) if hasattr(obj, "keys") else obj
    return {}


def handle_account_updated(data: dict[str, Any]) -> bool:
    """
    Process account.updated: update our account status from Stripe Connect.
    RESTRICTED when Stripe has created the deferred account (first update from NEW).
    VERIFIED when details_submitted and charges_enabled (onboarding complete).
    """
    obj = data.get("object")
    if not obj:
        return False
    obj = _to_dict(obj)
    stripe_account_id = obj.get("id")
    if not stripe_account_id or not stripe_account_id.startswith("acct_"):
        return False

    accounts_repo = StripeAccountRepository()
    record = accounts_repo.get_by_stripe_account_id(stripe_account_id)
    if not record:
        logger.debug("Webhook account.updated: no local account for %s", stripe_account_id)
        return False

    details_submitted = bool(obj.get("details_submitted"))
    charges_enabled = bool(obj.get("charges_enabled"))
    if details_submitted and charges_enabled:
        new_status = StripeAccountStatus.VERIFIED
    elif record.status == StripeAccountStatus.NEW:
        new_status = StripeAccountStatus.RESTRICTED
    else:
        return True

    if new_status == record.status:
        return True
    try:
        accounts_repo.update_status(record.user_id, new_status)
        logger.info(
            "Webhook account.updated: user_id=%s stripe_account_id=%s status=%s",
            record.user_id,
            stripe_account_id,
            new_status,
        )
        if new_status == StripeAccountStatus.VERIFIED:
            pending = accounts_repo.get_pending_earnings(record.user_id)
            transferred_currencies: list[str] = []
            for currency, amount in pending.items():
                if amount <= 0:
                    continue
                try:
                    stripe.Transfer.create(
                        amount=amount,
                        currency=currency,
                        destination=stripe_account_id,
                    )
                    transferred_currencies.append(currency)
                    logger.info(
                        "Webhook account.updated: transferred pending user_id=%s currency=%s amount=%s",
                        record.user_id,
                        currency,
                        amount,
                    )
                except stripe.StripeError as e:
                    logger.exception(
                        "Webhook account.updated: transfer failed user_id=%s currency=%s: %s",
                        record.user_id,
                        currency,
                        e,
                    )
            if transferred_currencies:
                accounts_repo.clear_pending_earnings(
                    record.user_id, only_currencies=transferred_currencies
                )
    except Exception as e:
        logger.exception("Webhook account.updated: failed to update status: %s", e)
        return False
    return True
