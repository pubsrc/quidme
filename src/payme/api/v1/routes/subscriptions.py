"""Subscription links routes."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, HTTPException

from payme.api.dependencies import (
    get_stripe_link_service,
    get_stripe_platform_account_service,
    get_subscriptions_repository,
    require_principal,
)
from payme.api.utils import normalize_expiry_date, require_fields_from_item, stripe_error_message
from payme.core.auth import Principal
from payme.db.repositories import SubscriptionsRepository
from payme.models.payment import DisableLinkResponse, PaymentLinkResponse, SubscriptionCreate
from payme.services.fees import amount_with_subscription_fee
from payme.services.payment_links import StripePaymentLinkService
from payme.services.stripe_platform_account_service import StripePlatformAccountService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
logger = logging.getLogger(__name__)


@router.post("", response_model=PaymentLinkResponse)
def create_subscription_link(
    payload: SubscriptionCreate,
    principal: Annotated[Principal, Depends(require_principal())],
    subs_repository: Annotated[SubscriptionsRepository, Depends(get_subscriptions_repository)],
    link_service: Annotated[StripePaymentLinkService, Depends(get_stripe_link_service)],
) -> PaymentLinkResponse:
    """
    Create a subscription (recurring) payment link. Factory returns platform or connected service based on account status (VERIFIED -> connected).
    """
    subscription_id = str(uuid.uuid4())
    total_charge, service_fee_percent, stripe_fee_percent = amount_with_subscription_fee(payload.amount)
    service_fee_cents = int(round(total_charge * service_fee_percent / 100))  # for DB and response

    subs_repository.create_draft(
        subscription_id=subscription_id,
        user_id=principal.user_id,
        title=payload.title,
        description=payload.description,
        amount=payload.amount,
        currency=payload.currency.value,
        interval=payload.interval.value,
        expires_at=normalize_expiry_date(payload.expires_at),
        require_fields=payload.require_fields,
    )

    try:
        stripe_link = link_service.create_payment_link_subscription(
            link_id=subscription_id,
            title=payload.title or "Subscription",
            description=payload.description,
            amount=total_charge,
            base_amount=payload.amount,
            currency=payload.currency.value,
            interval=payload.interval.value,
            require_fields=payload.require_fields,
            service_fee_percent=service_fee_percent,
        )  # application_fee_percent = service_fee only (platform)
    except stripe.error.StripeError as exc:
        logger.exception("Failed to create Stripe subscription link", extra={"subscription_id": subscription_id})
        raise HTTPException(status_code=400, detail=stripe_error_message(exc)) from exc

    on_platform = link_service.is_platform
    try:
        subs_repository.update_with_stripe(
            subscription_id=subscription_id,
            stripe_payment_link_id=stripe_link["id"],
            url=stripe_link["url"],
            service_fee=service_fee_cents,
            on_platform=on_platform,
        )
    except Exception as exc:
        logger.exception(
            "Failed to update subscription link with Stripe data",
            extra={"subscription_id": subscription_id},
        )
        try:
            link_service.disable_payment_link(stripe_link["id"])
        except stripe.error.StripeError:
            pass
        raise HTTPException(status_code=500, detail="Failed to save subscription link") from exc

    return PaymentLinkResponse(
        id=subscription_id,
        stripe_payment_link_id=stripe_link["id"],
        url=stripe_link["url"],
        title=payload.title,
        description=payload.description,
        amount=payload.amount,
        service_fee=service_fee_cents,
        currency=payload.currency,
        status="ACTIVE",
        expires_at=payload.expires_at,
        created_at=datetime.now(timezone.utc),
        total_amount_paid=0,
        earnings_amount=0,
        interval=payload.interval.value,
        require_fields=payload.require_fields,
    )


@router.get("", response_model=list[PaymentLinkResponse])
def list_subscription_links(
    principal: Annotated[Principal, Depends(require_principal())],
    subs_repository: Annotated[SubscriptionsRepository, Depends(get_subscriptions_repository)],
) -> list[PaymentLinkResponse]:
    """List subscription links for the current user. Earnings/totals updated by invoice.paid webhook."""
    items = subs_repository.list_by_user(principal.user_id)

    responses: list[PaymentLinkResponse] = []
    for item in items:
        if not item.get("stripe_payment_link_id") or not item.get("url"):
            continue
        expires_at = None
        if item.get("expires_at"):
            expires_at = datetime.fromtimestamp(int(item["expires_at"]), tz=timezone.utc).date()
        created_at = None
        if item.get("created_at"):
            created_at = datetime.fromisoformat(item["created_at"])
        total_paid = item.get("total_amount_paid")
        earnings = item.get("earnings_amount")
        if total_paid is None:
            total_paid = 0
        if earnings is None:
            earnings = 0
        responses.append(
            PaymentLinkResponse(
                id=item["subscription_id"],
                stripe_payment_link_id=item["stripe_payment_link_id"],
                url=item["url"],
                title=item.get("title"),
                description=item.get("description"),
                amount=item["amount"],
                service_fee=item.get("service_fee", 0),
                currency=item["currency"],
                interval=item.get("interval"),
                status=item.get("status", "ACTIVE"),
                expires_at=expires_at,
                created_at=created_at,
                total_amount_paid=int(total_paid),
                earnings_amount=int(earnings),
                require_fields=require_fields_from_item(item),
            )
        )
    min_dt = datetime.min.replace(tzinfo=timezone.utc)
    responses.sort(key=lambda link: link.created_at or min_dt, reverse=True)
    return responses


@router.post("/{subscription_id}/disable", response_model=DisableLinkResponse)
def disable_subscription_link(
    subscription_id: str,
    principal: Annotated[Principal, Depends(require_principal())],
    subs_repository: Annotated[SubscriptionsRepository, Depends(get_subscriptions_repository)],
    stripe_platform_service: Annotated[type[StripePlatformAccountService], Depends(get_stripe_platform_account_service)],
    link_service: Annotated[StripePaymentLinkService, Depends(get_stripe_link_service)],
) -> DisableLinkResponse:
    link = subs_repository.get(subscription_id)
    if not link or link.get("user_id") != principal.user_id:
        raise HTTPException(status_code=404, detail="Subscription link not found")
    if not link.get("stripe_payment_link_id"):
        raise HTTPException(status_code=400, detail="Subscription link not yet active")

    if link.get("on_platform"):
        stripe_platform_service.disable_platform_payment_link(link["stripe_payment_link_id"])
    else:
        link_service.disable_payment_link(link["stripe_payment_link_id"])
    subs_repository.mark_disabled(subscription_id)
    return DisableLinkResponse(id=subscription_id, status="DISABLED")
