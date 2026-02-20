"""Account (Stripe Connect) routes: get account, onboarding link, delete account."""

from __future__ import annotations

import logging
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, HTTPException, status

from payme.api.dependencies import (
    get_payment_links_repository,
    get_stripe_accounts_repository,
    get_stripe_platform_account_service,
    get_stripe_subscriptions_repository,
    get_subscriptions_repository,
    get_transactions_repository,
    get_users_repository,
    require_principal,
)
from payme.core.auth import Principal
from payme.core.cognito import delete_user as cognito_delete_user
from payme.db.repositories import (
    PaymentLinksRepository,
    StripeSubscriptionsRepository,
    StripeAccountRepository,
    SubscriptionsRepository,
    TransactionsRepository,
    UsersRepository,
)
from payme.models.user import OnboardingLinkResponse
from payme.services.stripe_platform_account_service import StripePlatformAccountService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/account")
def get_account(
    principal: Annotated[Principal, Depends(require_principal())],
    stripe_accounts_repository: Annotated[StripeAccountRepository, Depends(get_stripe_accounts_repository)],
) -> dict:
    """Return current user's Stripe Connect account (status, pending_earnings, earnings). get_principal ensures account exists."""
    rec = principal.stripe_account
    pending = stripe_accounts_repository.get_pending_earnings(principal.user_id)
    earnings = stripe_accounts_repository.get_earnings(principal.user_id)
    return {
        "stripe_account_id": rec.stripe_account_id,
        "country": rec.country or "",
        "status": rec.status or "NEW",
        "created_at": rec.created_at or "",
        "pending_earnings": pending,
        "earnings": earnings,
    }


@router.post("/onboarding", response_model=OnboardingLinkResponse)
def create_onboarding_link(
    principal: Annotated[Principal, Depends(require_principal())],
    stripe_platform_service: Annotated[type[StripePlatformAccountService], Depends(get_stripe_platform_account_service)],
) -> OnboardingLinkResponse:
    """Generate Stripe onboarding link for the connected account (platform creates the link). get_principal ensures account exists."""
    try:
        onboarding_url = stripe_platform_service.create_account_link(principal.stripe_account_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return OnboardingLinkResponse(onboarding_url=onboarding_url)


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    principal: Annotated[Principal, Depends(require_principal(None))],
    users_repository: Annotated[UsersRepository, Depends(get_users_repository)],
    stripe_accounts_repository: Annotated[StripeAccountRepository, Depends(get_stripe_accounts_repository)],
    payment_links_repository: Annotated[PaymentLinksRepository, Depends(get_payment_links_repository)],
    subscriptions_repository: Annotated[SubscriptionsRepository, Depends(get_subscriptions_repository)],
    stripe_subscriptions_repository: Annotated[StripeSubscriptionsRepository, Depends(get_stripe_subscriptions_repository)],
    transactions_repository: Annotated[TransactionsRepository, Depends(get_transactions_repository)],
    stripe_platform_service: Annotated[type[StripePlatformAccountService], Depends(get_stripe_platform_account_service)],
) -> None:
    """
    Delete all data for the authenticated user: DynamoDB (except user_identities),
    Stripe Connect account, and Cognito user. Only data for the current user is deleted.
    """
    user_id = principal.user_id
    external_sub = principal.external_sub
    stripe_account_id = principal.stripe_account_id

    # 1. Delete Stripe Connect account (if any)
    if stripe_account_id and stripe_account_id.strip().startswith("acct_"):
        try:
            stripe_platform_service.delete_connected_account(stripe_account_id)
        except stripe.InvalidRequestError as e:
            if "No such account" in str(e) or "deleted" in str(e).lower():
                logger.info("Stripe account %s already deleted or not found, continuing", stripe_account_id)
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to delete Stripe account",
                ) from e

    # 2. Delete DynamoDB data for this user only (order: child data first, then stripe_accounts, then users)
    transactions_repository.delete_all_for_user(user_id)
    payment_links_repository.delete_all_for_user(user_id)
    subscriptions_repository.delete_all_for_user(user_id)
    stripe_subscriptions_repository.delete_all_for_user(user_id)
    stripe_accounts_repository.delete(user_id)
    users_repository.delete(user_id)
    # user_identities intentionally not deleted per requirement

    # 3. Delete user from Cognito (so they can no longer sign in)
    try:
        cognito_delete_user(external_sub)
    except Exception as e:
        logger.exception("Cognito delete_user failed for sub=%s: %s", external_sub, e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="User data was deleted but failed to remove Cognito user",
        ) from e
