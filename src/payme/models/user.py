from __future__ import annotations

from pydantic import BaseModel


class User(BaseModel):
    user_id: str
    email: str | None = None
    stripe_account_id: str | None = None


class ConnectAccountRequest(BaseModel):
    """Request body for POST /platform/connected-accounts. Country is required (ISO 3166-1 alpha-2)."""
    country: str


class ConnectAccountResponse(BaseModel):
    stripe_account_id: str
    onboarding_url: str | None = None


class AccountResponse(BaseModel):
    """User's Stripe Connect account. status: NEW | RESTRICTED | VERIFIED."""

    stripe_account_id: str
    country: str
    status: str  # NEW, RESTRICTED, VERIFIED
    created_at: str


class OnboardingLinkResponse(BaseModel):
    onboarding_url: str
