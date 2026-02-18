"""Manual transfers routes: move pending earnings to the user's connected Stripe account."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from payme.api.dependencies import (
    get_stripe_accounts_repository,
    get_stripe_platform_account_service,
    require_principal,
)
from payme.core.auth import Principal
from payme.db.repositories import StripeAccountRepository
from payme.services.stripe_platform_account_service import StripePlatformAccountService

router = APIRouter(prefix="/transfers", tags=["transfers"])
logger = logging.getLogger(__name__)


@router.post("/transfer")
def transfer_pending_earnings(
    principal: Annotated[Principal, Depends(require_principal())],
    stripe_accounts_repository: Annotated[StripeAccountRepository, Depends(get_stripe_accounts_repository)],
    stripe_platform_service: Annotated[
        type[StripePlatformAccountService],
        Depends(get_stripe_platform_account_service),
    ],
) -> dict:
    """
    Transfer current user's pending earnings to their connected Stripe account.
    """
    stripe_account_id = principal.stripe_account_id
    if not stripe_account_id or not stripe_account_id.startswith("acct_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connected Stripe account is required",
        )

    pending = stripe_accounts_repository.get_pending_earnings(principal.user_id)
    if not pending:
        return {
            "stripe_account_id": stripe_account_id,
            "transferred": {},
            "failed": {},
            "message": "No pending earnings to transfer",
        }

    transferred: dict[str, float] = {}
    failed: dict[str, str] = {}
    transferred_currencies: list[str] = []

    for currency, amount in pending.items():
        if amount <= 0:
            continue
        # Store amounts as float in app; Stripe Transfer requires integer minor units.
        amount_minor = int(round(float(amount) * 100))
        if amount_minor <= 0:
            continue
        try:
            stripe_platform_service.create_transfer(
                amount=amount_minor,
                currency=currency,
                destination=stripe_account_id,
            )
            transferred[currency] = float(amount)
            transferred_currencies.append(currency)
        except Exception as exc:
            failed[currency] = str(exc)
            logger.exception(
                "Manual transfer failed for user_id=%s currency=%s amount=%s",
                principal.user_id,
                currency,
                amount,
            )

    if transferred_currencies:
        stripe_accounts_repository.clear_pending_earnings(
            principal.user_id,
            only_currencies=transferred_currencies,
        )

    if not transferred and failed:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "Transfer failed",
                "failed": failed,
            },
        )

    return {
        "stripe_account_id": stripe_account_id,
        "transferred": transferred,
        "failed": failed,
    }
