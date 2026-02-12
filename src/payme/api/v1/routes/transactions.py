"""Transactions and refunds routes."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query

from payme.api.dependencies import require_principal
from payme.core.auth import Principal
from payme.core.settings import settings
from payme.db.repositories import TransactionsRepository
from payme.models.transaction import Transaction, TransactionsResponse

router = APIRouter(prefix="/transactions", tags=["transactions"])
logger = logging.getLogger(__name__)


def _item_to_transaction(item: dict) -> Transaction:
    """Map DynamoDB item to Transaction model. id = payment_intent_id for frontend."""
    created_at = item.get("created_at")
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            created_at = datetime.utcnow()
    return Transaction(
        id=item.get("payment_intent_id", ""),
        amount=item.get("amount", 0),
        currency=item.get("currency", "usd"),
        status=item.get("status", ""),
        created_at=created_at,
        refunded=item.get("refunded", False),
        refund_status=item.get("refund_status"),
        customer_name=item.get("customer_name"),
        customer_email=item.get("customer_email"),
        customer_phone=item.get("customer_phone"),
        customer_address=item.get("customer_address"),
    )


@router.get("", response_model=TransactionsResponse)
def list_transactions(
    principal: Annotated[Principal, Depends(require_principal())],
    date_start: Annotated[str | None, Query(description="Start date YYYY-MM-DD")] = None,
    date_end: Annotated[str | None, Query(description="End date YYYY-MM-DD")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> TransactionsResponse:
    """List transactions for the current user. Without date range returns most recent (up to limit, default 25)."""
    repo = TransactionsRepository()
    if not date_start or not date_end:
        # Default: show most recent transactions (e.g. 25 on page load)
        cap = min(limit, 25)
        items = repo.list_recent(user_id=principal.user_id, limit=cap)
        transactions = [_item_to_transaction(item) for item in items]
        return TransactionsResponse(
            items=transactions,
            has_more=len(items) == cap,
            next_cursor=items[-1]["date_transaction_id"] if items else None,
        )
    if date_start > date_end:
        return TransactionsResponse(items=[], has_more=False, next_cursor=None)
    items = repo.list_by_user_and_date_range(
        user_id=principal.user_id,
        date_start=date_start,
        date_end=date_end,
        limit=limit,
    )
    transactions = [_item_to_transaction(item) for item in items]
    has_more = len(items) == limit
    next_cursor = items[-1]["date_transaction_id"] if has_more and items else None
    return TransactionsResponse(
        items=transactions,
        has_more=has_more,
        next_cursor=next_cursor,
    )


@router.get("/by-id/{payment_intent_id}", response_model=dict)
def get_transaction(
    payment_intent_id: str,
    principal: Annotated[Principal, Depends(require_principal())],
) -> dict:
    """Get a single transaction by payment_intent_id (for detail view)."""
    repo = TransactionsRepository()
    item = repo.get_by_payment_intent_id(principal.user_id, payment_intent_id)
    if not item:
        raise HTTPException(status_code=404, detail="Transaction not found")
    tx = _item_to_transaction(item)
    # Return full item for detail view (include link_id, stripe_account_id if needed by UI)
    out = tx.model_dump()
    out["link_id"] = item.get("link_id")
    out["date_transaction_id"] = item.get("date_transaction_id")
    return out
