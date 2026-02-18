from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class StripeCustomerAddress(BaseModel):
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None


class StripeCustomerDetails(BaseModel):
    id: str | None = None
    email: str | None = None
    name: str | None = None
    phone: str | None = None
    address: StripeCustomerAddress | None = None


class StripeSubscriptionPlan(BaseModel):
    amount: float | None = None
    currency: str | None = None
    interval: str | None = None


class StripeSubscriptionItem(BaseModel):
    id: str
    status: str
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool | None = None
    customer: StripeCustomerDetails | None = None
    plan: StripeSubscriptionPlan | None = None


class StripeSubscriptionsResponse(BaseModel):
    items: list[StripeSubscriptionItem]
    has_more: bool
    next_cursor: str | None = None


class CancelSubscriptionResponse(BaseModel):
    id: str
    status: str
