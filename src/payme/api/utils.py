"""Shared API utilities."""

from __future__ import annotations
from datetime import date, datetime, time, timezone

import stripe


def normalize_expiry_date(expires_at: date | None) -> datetime | None:
    if not expires_at:
        return None
    return datetime.combine(expires_at, time(23, 59, 59), tzinfo=timezone.utc)


def stripe_error_message(exc: stripe.error.StripeError) -> str:
    user_message = getattr(exc, "user_message", None)
    if user_message:
        return str(user_message)
    stripe_error = getattr(exc, "error", None)
    message = getattr(stripe_error, "message", None)
    if message:
        return str(message)
    return str(exc)


def require_fields_from_item(item: dict) -> list[str]:
    """Return require_fields list from a link/subscription item; supports legacy bool attributes."""
    if item.get("require_fields"):
        return list(item["require_fields"])
    out: list[str] = []
    if item.get("require_email"):
        out.append("email")
    if item.get("require_name"):
        out.append("name")
    if item.get("require_address"):
        out.append("address")
    if item.get("require_phone"):
        out.append("phone")
    return out
