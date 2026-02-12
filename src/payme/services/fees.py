"""
Centralized additive fee calculation for payment links.

Canonical fee model (SOURCE OF TRUTH):

Let:
    combined_pct = service_fee_percent + stripe_fee_percent
    multiplier = 1 + combined_pct / 100

Then:

    total = amount * multiplier + fixed_fee

Service fee:
    service_fee = fixed_fee / 2 + (service_fee_percent% of amount)

All other functions derive from this model.
"""

from __future__ import annotations

import math
from payme.core.settings import settings


# -------------------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------------------


def _multiplier(service_fee_percent: float, stripe_fee_percent: float) -> float:
    combined_pct = service_fee_percent + stripe_fee_percent
    return 1 + combined_pct / 100


def subtract_fees(amount: int, fee_cents: int) -> int:
    """Earnings after subtracting a fee."""
    if amount < 0:
        raise ValueError("amount must be non-negative")
    if fee_cents < 0:
        raise ValueError("fee must be non-negative")
    return max(amount - fee_cents, 0)


# -------------------------------------------------------------------------
# SOURCE OF TRUTH
# -------------------------------------------------------------------------


def amount_with_fee(
    amount_cents: int,
) -> tuple[int, float, float, int]:
    """
    Canonical additive fee model.

    Returns:
        (
            total_cents,
            effective_service_fee_percent,
            stripe_fee_percent,
            service_fee_cents,
        )
    """

    if amount_cents < 0:
        raise ValueError("amount_cents must be non-negative")

    fixed = settings.fixed_fee
    svc_pct = settings.service_fee_percent
    stripe_pct = settings.stripe_fee_percent

    multiplier = _multiplier(svc_pct, stripe_pct)

    # Total customer pays
    total_cents = int(round(amount_cents * multiplier + fixed))

    # Service fee amount
    service_fee_cents = int(
        round((fixed / 2) + (amount_cents * svc_pct / 100))
    )

    # Effective service % relative to base amount
    effective_service_pct = (
        (service_fee_cents / amount_cents) * 100
        if amount_cents > 0
        else 0.0
    )

    return (
        total_cents,
        effective_service_pct,
        stripe_pct,
        service_fee_cents,
    )


# -------------------------------------------------------------------------
# Reverse calculation
# -------------------------------------------------------------------------


def base_amount_from_total(total_cents: int) -> int:
    """
    Reverse of amount_with_fee().
    Returns original base amount before fees.
    """

    if total_cents < 0:
        raise ValueError("total_cents must be non-negative")

    fixed = settings.fixed_fee
    svc_pct = settings.service_fee_percent
    stripe_pct = settings.stripe_fee_percent

    multiplier = _multiplier(svc_pct, stripe_pct)

    base_amount = (total_cents - fixed) / multiplier

    return int(round(base_amount))


# -------------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------------


def amount_with_subscription_fee(
    amount_cents: int,
) -> tuple[int, float, float]:
    """
    Subscription links use same additive model.
    """

    total, effective_service_pct, stripe_pct, _ = amount_with_fee(
        amount_cents
    )

    return (total, effective_service_pct, stripe_pct)


def earnings_from_payment(
    total_paid_cents: int,
) -> int:
    """
    Seller earnings derived from canonical model.

    Process:
        1. Reverse total -> base amount
        2. Recompute canonical fees
        3. Subtract fixed + service + stripe
    """

    if total_paid_cents < 0:
        raise ValueError("total_paid_cents must be non-negative")

    fixed = settings.fixed_fee
    svc_pct = settings.service_fee_percent
    stripe_pct = settings.stripe_fee_percent

    # Recover original base amount
    base_amount = base_amount_from_total(total_paid_cents)

    # Recompute service fee deterministically
    _, _, _, service_fee_cents = amount_with_fee(base_amount)

    # Stripe fee (applied to base amount in this model)
    stripe_fee_cents = int(round(base_amount * stripe_pct / 100))

    earnings = (
        total_paid_cents
        - fixed
        - service_fee_cents
        - stripe_fee_cents
    )

    return max(earnings, 0)


# -------------------------------------------------------------------------
# Backwards-compatible aliases
# -------------------------------------------------------------------------


def subtract_service_fee(amount: int, service_fee: int) -> int:
    """Prefer subtract_fees for new code."""
    return subtract_fees(amount, service_fee)
