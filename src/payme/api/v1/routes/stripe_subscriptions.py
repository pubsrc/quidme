"""Customer subscriptions routes (captured from Stripe webhooks)."""

from __future__ import annotations

from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from payme.api.dependencies import require_principal
from payme.core.auth import Principal
from payme.models.stripe_subscription import CancelSubscriptionResponse, StripeSubscriptionsResponse
from payme.services.stripe_subscriptions_service import StripeSubscriptionsService

router = APIRouter(prefix="/stripe-subscriptions", tags=["stripe-subscriptions"])


class CancelSubscriptionRequest(BaseModel):
    subscription_id: str


@router.get("", response_model=StripeSubscriptionsResponse)
def list_customer_subscriptions(
    principal: Annotated[Principal, Depends(require_principal())],
    limit: int = Query(default=25, ge=1, le=100),
    page: str | None = Query(default=None),
) -> StripeSubscriptionsResponse:
    return StripeSubscriptionsService.list_user_subscriptions(
        principal.user_id, limit=limit, page=page
    )


@router.put("/cancellations", response_model=CancelSubscriptionResponse)
def cancel_customer_subscription(
    payload: CancelSubscriptionRequest,
    principal: Annotated[Principal, Depends(require_principal())],
) -> CancelSubscriptionResponse:
    try:
        return StripeSubscriptionsService.cancel_subscription_for_user(
            user_id=principal.user_id,
            subscription_id=payload.subscription_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except stripe.StripeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# Backward compatibility for existing frontend client.
@router.post("/{subscription_id}/cancel", response_model=CancelSubscriptionResponse)
def cancel_customer_subscription_legacy(
    subscription_id: str,
    principal: Annotated[Principal, Depends(require_principal())],
) -> CancelSubscriptionResponse:
    try:
        return StripeSubscriptionsService.cancel_subscription_for_user(
            user_id=principal.user_id,
            subscription_id=subscription_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except stripe.StripeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

