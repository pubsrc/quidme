"""Shared helpers for payment link payloads (require_fields, product name)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from payme.core.settings import settings

STRIPE_REQUIRE_FIELDS = frozenset({"email", "name", "address", "phone"})


def normalize_require_fields(fields: list[str]) -> frozenset[str]:
    """Return only Stripe-supported field names (lowercased)."""
    return frozenset(f.strip().lower() for f in fields if isinstance(f, str) and f.strip()) & STRIPE_REQUIRE_FIELDS


def apply_require_fields_to_payload(
    payload: dict[str, Any],
    require_fields: list[str],
    *,
    recurring: bool = False,
) -> None:
    """Mutate payload with Stripe collection options for the given require_fields."""
    allowed = normalize_require_fields(require_fields)
    if "email" in allowed and not recurring:
        payload["customer_creation"] = "always"
    if "address" in allowed:
        payload["billing_address_collection"] = "required"
    if "phone" in allowed:
        payload["phone_number_collection"] = {"enabled": True}
    if "name" in allowed:
        payload["name_collection"] = {
            "individual": {"enabled": True},
            "business": {"enabled": True, "optional": True},
        }


def product_name(title: str, link_type: str = "one_time") -> str:
    """Name shown in Stripe: TEST_... in test env, otherwise user title or default."""
    if settings.payme_env == "test":
        return f"TEST_{datetime.now(timezone.utc).strftime('%Y_%m_%d_%H_%M')}"
    return title or ("Payment" if link_type == "one_time" else "Subscription")
