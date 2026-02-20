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


@router.post("/platform/stripe", status_code=200)
async def stripe_webhook(request: Request) -> Response:
    """
    Receive Stripe webhook events (platform and Connect).
    Same pattern as Stripe's example: raw payload + Stripe-Signature header,
    then stripe.Webhook.construct_event(payload, sig_header, endpoint_secret).
    """
    # Raw body only — must not be parsed or modified before verification
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not settings.stripe_webhook_secret:
        logger.warning("Webhook received but no STRIPE_WEBHOOK_SECRET configured")
        return Response(status_code=500)

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.stripe_webhook_secret,
        )
    except ValueError as e:
        logger.warning("Webhook invalid payload: %s", e)
        return Response(status_code=400)
    except stripe.SignatureVerificationError as e:
        logger.warning("Webhook signature verification failed: %s", e)
        return Response(status_code=401)

    event_type = getattr(event, "type", None) or (event.get("type") if isinstance(event, dict) else None)
    if not event_type:
        return Response(status_code=200)

    data = getattr(event, "data", None) or (event.get("data") if isinstance(event, dict) else None)
    account_id = getattr(event, "account", None) or (event.get("account") if isinstance(event, dict) else None)
    if data is not None:
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

    return Response(status_code=200)
