"""
Centralized additive fee calculation for payment links.

Fee model (SOURCE OF TRUTH):

Let:
    combined_pct = service_fee_percent + stripe_fee_percent

Then the customer-facing total is computed by "grossing up" the base amount:

    total = (amount + fixed_fee) / (1 - combined_pct/100)

The platform service fee is a percentage of the *total*:

    service_fee_cents = total * service_fee_percent/100

This matches the unit-test expectations and keeps a single consistent model for:
1. Creating links (compute total + service_fee).
2. Earning computation on payment events (compute earnings from total paid).
"""

from __future__ import annotations

import math
from payme.core.settings import settings


# -------------------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------------------


def _multiplier(service_fee_percent: float, stripe_fee_percent: float) -> float:
    combined_pct = service_fee_percent + stripe_fee_percent
    if combined_pct >= 100:
        raise ValueError("combined percentage must be < 100")
    return 1 / (1 - combined_pct / 100)


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
    *,
    fixed_fee: int | None = None,
    service_fee_percent: float | None = None,
    stripe_fee_percent: float | None = None,
) -> tuple[int, float, float, int]:
    """
    Compute the customer-facing total for a base amount.

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

    fixed = settings.fixed_fee if fixed_fee is None else fixed_fee
    svc_pct = settings.service_fee_percent if service_fee_percent is None else service_fee_percent
    stripe_pct = settings.stripe_fee_percent if stripe_fee_percent is None else stripe_fee_percent

    multiplier = _multiplier(svc_pct, stripe_pct)
    total_cents = int(round((amount_cents + fixed) * multiplier))

    # Platform fee is defined as a percent of the total.
    service_fee_cents = int(round(total_cents * svc_pct / 100))
    effective_service_pct = float(svc_pct)

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
    base_amount = (total_cents / multiplier) - fixed

    return int(round(base_amount))


# -------------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------------


def amount_with_subscription_fee(
    amount_cents: int,
    *,
    fixed_fee: int | None = None,
    service_fee_percent: float | None = None,
    stripe_fee_percent: float | None = None,
) -> tuple[int, float, float]:
    """
    Subscription links use same additive model.
    """

    total, effective_service_pct, stripe_pct, _ = amount_with_fee(
        amount_cents,
        fixed_fee=fixed_fee,
        service_fee_percent=service_fee_percent,
        stripe_fee_percent=stripe_fee_percent,
    )

    return (total, effective_service_pct, stripe_pct)


def earnings_from_payment(
    total_paid_cents: int,
    *,
    known_service_fee_cents: int | None = None,
    fixed_fee: int | None = None,
    service_fee_percent: float | None = None,
    stripe_fee_percent: float | None = None,
) -> int:
    """
    Seller earnings derived from the fee model.

    If Stripe provides an application_fee_amount, pass it as known_service_fee_cents.
    Otherwise we compute service fee as a percentage of total_paid_cents.
    """

    if total_paid_cents < 0:
        raise ValueError("total_paid_cents must be non-negative")

    fixed = settings.fixed_fee if fixed_fee is None else fixed_fee
    svc_pct = settings.service_fee_percent if service_fee_percent is None else service_fee_percent
    stripe_pct = settings.stripe_fee_percent if stripe_fee_percent is None else stripe_fee_percent

    _multiplier(svc_pct, stripe_pct)  # validates combined_pct < 100

    service_fee_cents = (
        int(known_service_fee_cents)
        if known_service_fee_cents is not None
        else int(round(total_paid_cents * svc_pct / 100))
    )
    stripe_fee_cents = int(round(total_paid_cents * stripe_pct / 100))

    earnings = total_paid_cents - fixed - service_fee_cents - stripe_fee_cents

    return max(earnings, 0)


# -------------------------------------------------------------------------
# Backwards-compatible aliases
# -------------------------------------------------------------------------


def subtract_service_fee(amount: int, service_fee: int) -> int:
    """Prefer subtract_fees for new code."""
    return subtract_fees(amount, service_fee)
