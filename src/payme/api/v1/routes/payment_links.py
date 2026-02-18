"""Payment links routes."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, HTTPException

from payme.api.dependencies import (
    get_payment_links_repository,
    get_stripe_connected_account_link_service_optional,
    get_stripe_link_service,
    get_stripe_platform_account_service,
    get_stripe_platform_account_link_service,
    require_principal,
)
from payme.api.utils import normalize_expiry_date, require_fields_from_item, stripe_error_message
from payme.core.auth import Principal
from payme.db.repositories import PaymentLinksRepository
from payme.models.payment import (
    DisableLinkResponse,
    PaymentLinkCreate,
    PaymentLinkResponse,
)
from payme.services.fees import amount_with_fee, subtract_service_fee
from payme.services.payment_links import StripePaymentLinkService
from payme.services.stripe_event_handler import record_payment_succeeded_from_intent
from payme.services.stripe_platform_account_service import StripePlatformAccountService

router = APIRouter(prefix="/payment-links", tags=["payment-links"])
logger = logging.getLogger(__name__)


@router.post("", response_model=PaymentLinkResponse)
def create_payment_link(
    payload: PaymentLinkCreate,
    principal: Annotated[Principal, Depends(require_principal())],
    links_repository: Annotated[PaymentLinksRepository, Depends(get_payment_links_repository)],
    link_service: Annotated[StripePaymentLinkService, Depends(get_stripe_link_service)],
) -> PaymentLinkResponse:
    """
    Create a one-time payment link. Factory returns platform or connected service based on account status (VERIFIED -> connected).
    """
    link_id = str(uuid.uuid4())
    total_amount, service_fee_percent, stripe_fee_percent, service_fee_cents = amount_with_fee(payload.amount)
    links_repository.create_draft(
        link_id=link_id,
        user_id=principal.user_id,
        title=payload.title,
        description=payload.description,
        amount=payload.amount,
        currency=payload.currency.value,
        expires_at=normalize_expiry_date(payload.expires_at),
        link_type="one_time",
        require_fields=payload.require_fields,
    )

    try:
        stripe_link = link_service.create_payment_link_one_time(
            link_id=link_id,
            title=payload.title or "Payment",
            description=payload.description,
            amount=total_amount,
            base_amount=payload.amount,
            currency=payload.currency.value,
            require_fields=payload.require_fields,
            service_fee=service_fee_cents,
        )
    except stripe.error.StripeError as exc:
        logger.exception("Failed to create Stripe payment link", extra={"link_id": link_id})
        raise HTTPException(status_code=400, detail=stripe_error_message(exc)) from exc

    on_platform = link_service.is_platform
    try:
        links_repository.update_with_stripe(
            link_id=link_id,
            stripe_payment_link_id=stripe_link["id"],
            url=stripe_link["url"],
            service_fee=service_fee_cents,
            on_platform=on_platform,
        )
    except Exception as exc:
        logger.exception("Failed to update payment link with Stripe data", extra={"link_id": link_id})
        try:
            link_service.disable_payment_link(stripe_link["id"])
        except stripe.error.StripeError:
            pass
        raise HTTPException(status_code=500, detail="Failed to save payment link") from exc

    return PaymentLinkResponse(
        id=link_id,
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
        require_fields=payload.require_fields,
    )


@router.get("", response_model=list[PaymentLinkResponse])
def list_payment_links(
    principal: Annotated[Principal, Depends(require_principal())],
    links_repository: Annotated[PaymentLinksRepository, Depends(get_payment_links_repository)],
    platform_link_service: Annotated[StripePaymentLinkService, Depends(get_stripe_platform_account_link_service)],
    connected_link_service: Annotated[
        StripePaymentLinkService | None,
        Depends(get_stripe_connected_account_link_service_optional),
    ],
) -> list[PaymentLinkResponse]:
    """List payment links for the current user. Only returns links that have been fully created (have Stripe id/url)."""
    items = links_repository.list_by_user(principal.user_id)

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
        if total_paid is None or earnings is None:
            total_paid = 0
            earnings = 0
            link_service = platform_link_service if item.get("on_platform") else connected_link_service
            if link_service is not None:
                try:
                    intents = link_service.list_transactions_for_link(principal.user_id, item["link_id"])
                    account_id = link_service.stripe_account_id
                    for intent in intents.get("data", []):
                        if intent.get("status") != "succeeded":
                            continue
                        # Backfill: record payment so transactions list and stripe_account earnings stay in sync
                        try:
                            record_payment_succeeded_from_intent(intent, account_id=account_id)
                        except Exception:
                            logger.debug(
                                "Backfill record_payment_succeeded_from_intent failed for intent",
                                extra={"link_id": item["link_id"], "intent_id": intent.get("id")},
                                exc_info=True,
                            )
                        total_paid += intent.get("amount", 0)
                        earnings += subtract_service_fee(intent.get("amount", 0), item.get("service_fee", 0))
                except Exception:
                    logger.warning(
                        "Failed to list transactions for link; total_paid/earnings will be 0",
                        extra={"link_id": item["link_id"]},
                        exc_info=True,
                    )
        else:
            total_paid = int(total_paid)
            earnings = int(earnings)
        responses.append(
            PaymentLinkResponse(
                id=item["link_id"],
                stripe_payment_link_id=item["stripe_payment_link_id"],
                url=item["url"],
                title=item.get("title"),
                description=item.get("description"),
                amount=item["amount"],
                service_fee=item.get("service_fee", 0),
                currency=item["currency"],
                status=item.get("status", "ACTIVE"),
                expires_at=expires_at,
                created_at=created_at,
                total_amount_paid=total_paid,
                earnings_amount=earnings,
                require_fields=require_fields_from_item(item),
            )
        )
    min_dt = datetime.min.replace(tzinfo=timezone.utc)
    responses.sort(key=lambda link: link.created_at or min_dt, reverse=True)
    return responses


@router.post("/{link_id}/disable", response_model=DisableLinkResponse)
def disable_payment_link(
    link_id: str,
    principal: Annotated[Principal, Depends(require_principal())],
    links_repository: Annotated[PaymentLinksRepository, Depends(get_payment_links_repository)],
    stripe_platform_service: Annotated[type[StripePlatformAccountService], Depends(get_stripe_platform_account_service)],
    link_service: Annotated[StripePaymentLinkService, Depends(get_stripe_link_service)],
) -> DisableLinkResponse:
    link = links_repository.get(link_id)
    if not link or link.get("user_id") != principal.user_id:
        raise HTTPException(status_code=404, detail="Payment link not found")
    if not link.get("stripe_payment_link_id"):
        raise HTTPException(status_code=400, detail="Payment link not yet active")

    if link.get("on_platform"):
        stripe_platform_service.disable_platform_payment_link(link["stripe_payment_link_id"])
    else:
        link_service.disable_payment_link(link["stripe_payment_link_id"])
    links_repository.mark_disabled(link_id)
    return DisableLinkResponse(id=link_id, status="DISABLED")
