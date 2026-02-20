"""Stripe webhook endpoint for platform and Connect (v2) account events."""

from __future__ import annotations

import logging

import stripe
from fastapi import APIRouter, Request, Response

from payme.core.settings import settings
from payme.services.stripe_webhook import (
    ACCOUNT_UPDATED_EVENT,
    CHECKOUT_SESSION_COMPLETED_EVENT,
    INVOICE_PAID_EVENTS,
    PAYMENT_FAILED_EVENTS,
    PAYMENT_SUCCEEDED_EVENTS,
    SUBSCRIPTION_DELETED_EVENT,
    SUBSCRIPTION_UPDATED_EVENT,
    handle_account_updated,
    handle_checkout_session_completed,
    handle_invoice_paid,
    handle_payment_failed,
    handle_payment_succeeded,
    handle_subscription_lifecycle_event,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


def _dispatch_event(event_type: str, data: dict, account_id: str | None) -> None:
    if event_type in PAYMENT_SUCCEEDED_EVENTS:
        handle_payment_succeeded(event_type, data, account_id=account_id)
    elif event_type in PAYMENT_FAILED_EVENTS:
        handle_payment_failed(event_type, data, account_id=account_id)
    elif event_type in INVOICE_PAID_EVENTS:
        handle_invoice_paid(data, account_id=account_id)
    elif event_type in {SUBSCRIPTION_UPDATED_EVENT, SUBSCRIPTION_DELETED_EVENT}:
        handle_subscription_lifecycle_event(event_type, data, account_id=account_id)
    elif event_type == CHECKOUT_SESSION_COMPLETED_EVENT:
        handle_checkout_session_completed(data, account_id=account_id)
    elif event_type == ACCOUNT_UPDATED_EVENT:
        handle_account_updated(data)


async def _handle_stripe_webhook(request: Request, *, signing_secret: str, source: str) -> Response:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not signing_secret:
        logger.warning("Webhook received for %s but signing secret is not configured", source)
        return Response(status_code=500)
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            signing_secret,
        )
    except ValueError as e:
        logger.error("%s webhook invalid payload: %s", source, e)
        return Response(status_code=400)
    except stripe.SignatureVerificationError as e:
        logger.error("%s webhook signature verification failed: %s", source, e)
        return Response(status_code=401)

    event_type = getattr(event, "type", None) or (event.get("type") if isinstance(event, dict) else None)
    if not event_type:
        return Response(status_code=200)

    data = getattr(event, "data", None) or (event.get("data") if isinstance(event, dict) else None)
    account_id = getattr(event, "account", None) or (event.get("account") if isinstance(event, dict) else None)
    if data is not None:
        _dispatch_event(event_type, data, account_id)

    return Response(status_code=200)


@router.post("/platform/stripe", status_code=200)
async def platform_stripe_webhook(request: Request) -> Response:
    """
    Stripe webhook endpoint for platform account events.
    """
    logger.info("Processing Stripe webhook for platform accounts")
    return await _handle_stripe_webhook(
        request,
        signing_secret=settings.stripe_webhook_secret,
        source="platform",
    )


@router.post("/connected-accounts/stripe", status_code=200)
async def connected_accounts_stripe_webhook(request: Request) -> Response:
    """
    Stripe webhook endpoint for connected account events (Connect / Accounts v2).
    Handles the same events as platform route, including account.updated.
    """
    logger.info("Processing Stripe webhook for connected accounts")
    return await _handle_stripe_webhook(
        request,
        signing_secret=settings.stripe_connected_webhook_secret,
        source="connected-accounts",
    )
