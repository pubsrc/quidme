"""Platform Stripe operations: create Connect account (no connected account required)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from payme.api.dependencies import (
    get_stripe_accounts_repository,
    get_stripe_platform_account_service,
    get_users_repository,
    require_principal,
)
from payme.core.auth import Principal
from payme.db.repositories import StripeAccountRepository, UsersRepository
from payme.models.user import ConnectAccountRequest, ConnectAccountResponse
from payme.services.stripe_platform_account_service import StripePlatformAccountService

router = APIRouter(prefix="/platform", tags=["platform"])

# ISO 3166-1 alpha-2 country code length
_COUNTRY_CODE_LEN = 2


def _resolve_connect_country_and_email(
    body: ConnectAccountRequest,
    principal: Principal,
    users_repository: UsersRepository,
) -> tuple[str, str]:
    """Validate request and resolve country and email. Raises HTTPException on validation failure."""
    country = (body.country or "").strip().upper()
    if not country or len(country) != _COUNTRY_CODE_LEN:
        raise HTTPException(status_code=400, detail="country is required (ISO 3166-1 alpha-2)")
    email = (principal.email or "").strip()
    if not email:
        user_record = users_repository.get(principal.user_id)
        email = (user_record.email or "").strip() if user_record else ""
    if not email:
        raise HTTPException(status_code=400, detail="User email is required for connect")
    return country, email


@router.post("/connected-accounts", response_model=ConnectAccountResponse)
def create_connected_account(
    body: ConnectAccountRequest,
    principal: Annotated[Principal, Depends(require_principal(None))],
    users_repository: Annotated[UsersRepository, Depends(get_users_repository)],
    stripe_accounts_repository: Annotated[StripeAccountRepository, Depends(get_stripe_accounts_repository)],
    stripe_platform_service: Annotated[type[StripePlatformAccountService], Depends(get_stripe_platform_account_service)],
) -> ConnectAccountResponse:
    """
    Create or return the user's single Stripe Connect (deferred) account.
    One-to-one: a user has at most one Stripe account; never creates if one already exists.
    Country is required in the request body when creating.
    """
    if principal.stripe_account is not None and (principal.stripe_account_id or "").strip():
        return ConnectAccountResponse(
            stripe_account_id=principal.stripe_account.stripe_account_id or "",
            onboarding_url=None,
        )

    country, email = _resolve_connect_country_and_email(body, principal, users_repository)

    account_id = stripe_platform_service.create_custom_connected_account(email, country)
    if principal.stripe_account is not None:
        stripe_accounts_repository.update_stripe_account_id(principal.user_id, account_id)
    else:
        stripe_accounts_repository.create(principal.user_id, account_id, country)
    users_repository.update_stripe_account(principal.user_id, account_id)
    return ConnectAccountResponse(stripe_account_id=account_id, onboarding_url=None)
