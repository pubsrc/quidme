from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class Transaction(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
    created_at: datetime
    description: str | None = None
    refunded: bool = False
    refund_status: str | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    customer_address: str | None = None


class TransactionsResponse(BaseModel):
    items: list[Transaction]
    has_more: bool
    next_cursor: str | None = None
