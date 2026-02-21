"""Centralized additive fee calculation for payment links."""

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


_USD_TIER_THRESHOLDS_CENTS = (1000, 2000, 5000, 10000, 50000, 100000, 500000, 1000000)
_USD_TIER_FEES_CENTS = (40, 80, 200, 300, 1000, 2000, 4000, 6000, 10000)
_USD_TO_CURRENCY_RATE = {
    "usd": 1.0,
    "eur": 0.95,
    "gbp": 0.8,
    "bgn": 1.85,
    "ron": 4.7,
    "all": 95.0,
}


def _round_up_fee_major(value: float) -> float:
    """
    Round fee up to simple "human-friendly" tiers.
    This keeps fees predictable across currencies.
    """
    if value < 1:
        step = 0.2
    elif value < 5:
        step = 1.0
    elif value < 20:
        step = 5.0
    elif value < 50:
        step = 10.0
    else:
        step = 20.0
    return math.ceil(value / step) * step


def _tier_fixed_fee(amount_cents: int, currency: str) -> int:
    """
    Fixed fee schedule based on amount tiers (10, 20, 50, ... 10,000) in local currency.
    USD fee schedule is converted per currency and rounded to simple local steps.
    """
    normalized_currency = (currency or "usd").lower()
    fx = _USD_TO_CURRENCY_RATE.get(normalized_currency, 1.0)

    tier_index = len(_USD_TIER_THRESHOLDS_CENTS)  # final tier (> 10,000)
    for idx, threshold in enumerate(_USD_TIER_THRESHOLDS_CENTS):
        if amount_cents <= threshold:
            tier_index = idx
            break

    usd_fee_cents = _USD_TIER_FEES_CENTS[tier_index]
    converted_fee_major = (usd_fee_cents / 100.0) * fx
    rounded_fee_major = _round_up_fee_major(converted_fee_major)
    return int(round(rounded_fee_major * 100))


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
    currency: str = "gbp",
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

    fixed = _tier_fixed_fee(amount_cents, currency) if fixed_fee is None else fixed_fee
    # Service percentage is intentionally not charged anymore.
    svc_pct = 0.0
    stripe_pct = settings.stripe_fee_percent if stripe_fee_percent is None else stripe_fee_percent

    multiplier = _multiplier(svc_pct, stripe_pct)
    total_cents = int(round((amount_cents + fixed) * multiplier))

    # Platform fee is fixed per amount tier.
    service_fee_cents = fixed
    # Preserve a percent value for callers that still require it (e.g., subscription API).
    effective_service_pct = float((service_fee_cents * 100 / total_cents) if total_cents > 0 else 0.0)

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
    currency: str = "gbp",
    fixed_fee: int | None = None,
    service_fee_percent: float | None = None,
    stripe_fee_percent: float | None = None,
) -> tuple[int, float, float]:
    """
    Subscription links use same additive model.
    """

    total, effective_service_pct, stripe_pct, _ = amount_with_fee(
        amount_cents,
        currency=currency,
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
