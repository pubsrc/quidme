"""Refunds route."""

from __future__ import annotations

import logging
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, HTTPException

from payme.api.dependencies import require_principal
from payme.core.auth import Principal
from payme.core.settings import settings
from pydantic import BaseModel

from payme.db.repositories import TransactionsRepository

router = APIRouter(prefix="/refunds", tags=["refunds"])
logger = logging.getLogger(__name__)


class RefundRequest(BaseModel):
    payment_intent_id: str


@router.post("")
def create_refund(
    body: RefundRequest,
    principal: Annotated[Principal, Depends(require_principal())],
) -> dict:
    """Refund a payment and mark the transaction as refunded."""
    payment_intent_id = (body.payment_intent_id or "").strip()
    if not payment_intent_id:
        raise HTTPException(status_code=400, detail="payment_intent_id required")
    if not payment_intent_id.startswith("pi_"):
        payment_intent_id = f"pi_{payment_intent_id}"

    repo = TransactionsRepository()
    item = repo.get_by_payment_intent_id(principal.user_id, payment_intent_id)
    if not item:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if item.get("refunded"):
        return {"status": "already_refunded", "message": "Transaction already refunded"}
    if item.get("status") != "succeeded":
        raise HTTPException(status_code=400, detail="Only succeeded transactions can be refunded")

    stripe_account_id = item.get("stripe_account_id")
    stripe.api_key = settings.stripe_secret
    try:
        if stripe_account_id:
            stripe.Refund.create(
                payment_intent=payment_intent_id,
                stripe_account=stripe_account_id,
            )
        else:
            stripe.Refund.create(payment_intent=payment_intent_id)
    except stripe.StripeError as e:
        logger.warning("Refund failed for %s: %s", payment_intent_id, e)
        raise HTTPException(status_code=400, detail=str(e)) from e

    repo.mark_refunded(
        principal.user_id,
        item["date_transaction_id"],
        refund_status="refunded",
    )
    return {"status": "refunded", "payment_intent_id": payment_intent_id}
