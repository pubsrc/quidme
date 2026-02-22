"""Transfers routes."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator

from payme.api.dependencies import (
    get_stripe_accounts_repository,
    get_stripe_platform_account_service,
    require_principal,
)
from payme.core.auth import Principal
from payme.core.constants import StripeAccountStatus
from payme.db.repositories import StripeAccountRepository
from payme.services.stripe_platform_account_service import StripePlatformAccountService

router = APIRouter(prefix="/transfers", tags=["transfers"])
logger = logging.getLogger(__name__)


class PayoutScheduleRequest(BaseModel):
    interval: str = Field(..., description="daily | weekly | monthly | manual")
    weekly_anchor: str | None = Field(
        default=None,
        description="Required when interval=weekly. One of monday..sunday",
    )
    monthly_anchor: int | None = Field(
        default=None,
        ge=1,
        le=31,
        description="Required when interval=monthly. Day of month 1..31",
    )

    @model_validator(mode="after")
    def validate_schedule(self) -> "PayoutScheduleRequest":
        interval = (self.interval or "").strip().lower()
        allowed = {"daily", "weekly", "monthly", "manual"}
        if interval not in allowed:
            raise ValueError("interval must be one of: daily, weekly, monthly, manual")
        self.interval = interval

        if interval == "weekly":
            days = {
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            }
            day = (self.weekly_anchor or "").strip().lower()
            if day not in days:
                raise ValueError("weekly_anchor is required for weekly interval")
            self.weekly_anchor = day

        if interval == "monthly" and self.monthly_anchor is None:
            raise ValueError("monthly_anchor is required for monthly interval")

        if interval != "weekly":
            self.weekly_anchor = None
        if interval != "monthly":
            self.monthly_anchor = None
        return self


@router.post("/payouts")
def create_payouts(
    principal: Annotated[Principal, Depends(require_principal(StripeAccountStatus.VERIFIED))],
    stripe_accounts_repository: Annotated[StripeAccountRepository, Depends(get_stripe_accounts_repository)],
    stripe_platform_service: Annotated[
        type[StripePlatformAccountService],
        Depends(get_stripe_platform_account_service),
    ],
) -> dict:
    """
    Create payouts from the connected account's available Stripe balance to bank account.
    """
    stripe_account_id = principal.stripe_account_id
    if not stripe_account_id or not stripe_account_id.startswith("acct_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connected Stripe account is required",
        )

    result = stripe_platform_service.create_payouts_from_available_balance(stripe_account_id)
    transferred = result.get("transferred", {})
    failed = result.get("failed", {})
    payout_ids = result.get("payout_ids", {})

    if not transferred and failed:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "Payout failed",
                "failed": failed,
            },
        )

    if not transferred and not failed:
        logger.warning(
            "Payout requested but no available balance: user_id=%s stripe_account_id=%s",
            principal.user_id,
            stripe_account_id,
        )
        return {
            "stripe_account_id": stripe_account_id,
            "transferred": {},
            "failed": {},
            "payout_ids": {},
            "status": "no_balance",
            "message": "No available balance in the account to payout",
        }

    stripe_accounts_repository.clear_pending_earnings(principal.user_id)

    return {
        "stripe_account_id": stripe_account_id,
        "transferred": transferred,
        "failed": failed,
        "payout_ids": payout_ids,
        "status": "success",
    }


@router.post("/schedules")
def create_payout_schedule(
    payload: PayoutScheduleRequest,
    principal: Annotated[Principal, Depends(require_principal(StripeAccountStatus.VERIFIED))],
    stripe_platform_service: Annotated[
        type[StripePlatformAccountService],
        Depends(get_stripe_platform_account_service),
    ],
) -> dict:
    """
    Configure automatic payout schedule for user's connected Stripe account.
    """
    stripe_account_id = principal.stripe_account_id
    if not stripe_account_id or not stripe_account_id.startswith("acct_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connected Stripe account is required",
        )

    schedule = stripe_platform_service.update_payout_schedule(
        stripe_account_id=stripe_account_id,
        interval=payload.interval,
        weekly_anchor=payload.weekly_anchor,
        monthly_anchor=payload.monthly_anchor,
    )
    return {
        "stripe_account_id": stripe_account_id,
        "schedule": schedule,
    }
