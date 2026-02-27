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
    get_user_identities_repository,
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
    UserIdentitiesRepository,
    UsersRepository,
)
from payme.models.user import OnboardingLinkResponse
from payme.services.cloudwatch_metrics import record_transfer_results
from payme.services.stripe_platform_account_service import StripePlatformAccountService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/accounts", tags=["accounts"])


def _has_positive_pending(pending: dict[str, int]) -> bool:
    return any(int(amount) > 0 for amount in pending.values())


def _transfer_pending_earnings(
    *,
    user_id: str,
    stripe_account_id: str,
    pending: dict[str, int],
    stripe_accounts_repository: StripeAccountRepository,
    stripe_platform_service: type[StripePlatformAccountService],
) -> tuple[str, dict[str, int]]:
    """
    Attempt to move all positive pending earnings to the connected account.

    Returns:
        (pending_earnings_status, refreshed_pending)
        pending_earnings_status: "settled" if all attempted transfers succeeded, else "in_progress"
    """
    successful_transfers = 0
    failed_transfers = 0
    transferred_currencies: list[str] = []

    for currency, amount in pending.items():
        amount_minor = int(amount)
        if amount_minor <= 0:
            continue
        try:
            stripe_platform_service.create_transfer(
                amount=amount_minor,
                currency=currency,
                destination=stripe_account_id,
            )
            transferred_currencies.append(currency)
            successful_transfers += 1
        except Exception as exc:
            failed_transfers += 1
            logger.warning(
                "Failed transfer from account status endpoint user_id=%s stripe_account_id=%s currency=%s amount=%s: %s",
                user_id,
                stripe_account_id,
                currency,
                amount_minor,
                exc,
            )

    if transferred_currencies:
        stripe_accounts_repository.clear_pending_earnings(
            user_id, only_currencies=transferred_currencies
        )

    record_transfer_results(
        successful=successful_transfers,
        failed=failed_transfers,
    )

    refreshed_pending = stripe_accounts_repository.get_pending_earnings(user_id)
    pending_earnings_status = "in_progress" if failed_transfers > 0 else "settled"
    return pending_earnings_status, refreshed_pending


@router.get("/account")
def get_account(
    principal: Annotated[Principal, Depends(require_principal())],
    stripe_accounts_repository: Annotated[StripeAccountRepository, Depends(get_stripe_accounts_repository)],
    stripe_platform_service: Annotated[type[StripePlatformAccountService], Depends(get_stripe_platform_account_service)],
) -> dict:
    """Return current user's Stripe Connect account (status, pending_earnings, earnings). get_principal ensures account exists."""
    rec = principal.stripe_account
    pending = stripe_accounts_repository.get_pending_earnings(principal.user_id)
    pending_earnings_status = "settled"

    if _has_positive_pending(pending):
        pending_earnings_status, pending = _transfer_pending_earnings(
            user_id=principal.user_id,
            stripe_account_id=rec.stripe_account_id,
            pending=pending,
            stripe_accounts_repository=stripe_accounts_repository,
            stripe_platform_service=stripe_platform_service,
        )

    earnings = stripe_accounts_repository.get_earnings(principal.user_id)
    return {
        "stripe_account_id": rec.stripe_account_id,
        "country": rec.country or "",
        "status": rec.status or "NEW",
        "pending_earnings_status": pending_earnings_status,
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
    user_identities_repository: Annotated[UserIdentitiesRepository, Depends(get_user_identities_repository)],
    stripe_accounts_repository: Annotated[StripeAccountRepository, Depends(get_stripe_accounts_repository)],
    payment_links_repository: Annotated[PaymentLinksRepository, Depends(get_payment_links_repository)],
    subscriptions_repository: Annotated[SubscriptionsRepository, Depends(get_subscriptions_repository)],
    stripe_subscriptions_repository: Annotated[StripeSubscriptionsRepository, Depends(get_stripe_subscriptions_repository)],
    transactions_repository: Annotated[TransactionsRepository, Depends(get_transactions_repository)],
    stripe_platform_service: Annotated[type[StripePlatformAccountService], Depends(get_stripe_platform_account_service)],
) -> None:
    """
    Hard-delete all data for the authenticated user in FastAPI:
    DynamoDB records, Stripe Connect account (best-effort), and Cognito user.
    Only data for the current user is deleted.
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
                logger.exception(
                    "Failed to delete Stripe account user_id=%s stripe_account_id=%s",
                    user_id,
                    stripe_account_id,
                )
        except stripe.StripeError:
            logger.exception(
                "Failed to delete Stripe account user_id=%s stripe_account_id=%s",
                user_id,
                stripe_account_id,
            )
        except Exception:
            logger.exception(
                "Unexpected error deleting Stripe account user_id=%s stripe_account_id=%s",
                user_id,
                stripe_account_id,
            )

    # 2. Hard-delete DynamoDB data for this user only.
    transactions_repository.delete_all_for_user(user_id)
    payment_links_repository.delete_all_for_user(user_id)
    subscriptions_repository.delete_all_for_user(user_id)
    stripe_subscriptions_repository.delete_all_for_user(user_id)
    stripe_accounts_repository.delete(user_id)
    user_identities_repository.delete_all_for_user(user_id)
    users_repository.delete(user_id)

    # 3. Delete user from Cognito (so they can no longer sign in)
    try:
        cognito_delete_user(external_sub)
    except Exception as e:
        logger.exception("Cognito delete_user failed for sub=%s: %s", external_sub, e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="User data was deleted but failed to remove Cognito user",
        ) from e
