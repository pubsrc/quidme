from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class Currency(str, Enum):
    usd = "usd"
    eur = "eur"
    gbp = "gbp"


class RecurringInterval(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    year = "year"


# Stripe Payment Link supported require_fields; others in request are ignored.
REQUIRE_FIELDS_ALLOWED = frozenset({"email", "name", "address", "phone"})


class PaymentLinkCreate(BaseModel):
    """Only amount is mandatory; title, description, and require_fields are optional."""

    title: str | None = None
    description: str | None = None
    amount: int = Field(..., gt=0, description="Amount in minor units")
    currency: Currency = Currency.gbp
    expires_at: date | None = None
    require_fields: list[str] = Field(
        default_factory=list,
        description="Fields to collect at checkout: email, name, address, phone (unsupported names ignored)",
    )

    @field_validator("require_fields")
    @classmethod
    def normalize_require_fields(cls, value: list[str]) -> list[str]:
        if not value:
            return []
        normalized = [f.strip().lower() for f in value if isinstance(f, str) and f.strip()]
        return [f for f in normalized if f in REQUIRE_FIELDS_ALLOWED]

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class SubscriptionCreate(BaseModel):
    """Only amount and interval are mandatory; title and description are optional."""

    title: str | None = None
    description: str | None = None
    amount: int = Field(..., gt=0, description="Amount in minor units")
    currency: Currency = Currency.gbp
    interval: RecurringInterval
    expires_at: date | None = None
    require_fields: list[str] = Field(
        default_factory=list,
        description="Fields to collect at checkout: email, name, address, phone (unsupported names ignored)",
    )

    @field_validator("require_fields")
    @classmethod
    def normalize_require_fields(cls, value: list[str]) -> list[str]:
        if not value:
            return []
        normalized = [f.strip().lower() for f in value if isinstance(f, str) and f.strip()]
        return [f for f in normalized if f in REQUIRE_FIELDS_ALLOWED]

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class PaymentLinkResponse(BaseModel):
    id: str
    stripe_payment_link_id: str
    url: str
    title: str | None = None
    description: str | None = None
    amount: int
    service_fee: int
    currency: Currency
    interval: str | None = None
    status: str
    expires_at: date | None = None
    created_at: datetime | None = None
    total_amount_paid: int = 0
    earnings_amount: int = 0
    require_fields: list[str] = Field(default_factory=list, description="Fields required at checkout")


class TransactionDetail(BaseModel):
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


class PaymentLinkDetailResponse(BaseModel):
    link: PaymentLinkResponse
    transactions: list[TransactionDetail]


class DisableLinkResponse(BaseModel):
    id: str
    status: str


class RefundRequest(BaseModel):
    payment_intent_id: str
    reason: str | None = None


class RefundResponse(BaseModel):
    refund_id: str
    status: str
