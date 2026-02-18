"""Payment links created on a connected Stripe account (with application fee)."""

from __future__ import annotations

from typing import Any

import stripe

from payme.core.auth import Principal
from payme.core.settings import settings

from payme.services.payment_links.base import StripePaymentLinkService
from payme.services.payment_links.helpers import apply_require_fields_to_payload, product_name


class StripeConnectedAccountLinkService(StripePaymentLinkService):
    """
    Creates payment links on a connected account (with application fee).
    Can be constructed with Principal or from_account_id for disable/list (e.g. expire_links).
    """

    def __init__(
        self,
        principal: Principal | None = None,
        *,
        stripe_account_id: str | None = None,
    ) -> None:
        if principal is not None:
            self._principal = principal
            self._stripe_account_id = (principal.stripe_account_id or "").strip()
        elif stripe_account_id and stripe_account_id.strip().startswith("acct_"):
            self._principal = None  # type: ignore[assignment]
            self._stripe_account_id = stripe_account_id.strip()
        else:
            raise ValueError("Provide principal or stripe_account_id (acct_...)")

    @classmethod
    def from_account_id(cls, stripe_account_id: str) -> StripeConnectedAccountLinkService:
        """Build for disable_payment_link / list_transactions only (e.g. expire_links)."""
        return cls(principal=None, stripe_account_id=stripe_account_id)

    def _ensure_principal(self) -> Principal:
        if self._principal is None:
            raise RuntimeError("This operation requires a Principal.")
        return self._principal

    @property
    def is_platform(self) -> bool:
        return False

    @property
    def stripe_account_id(self) -> str | None:
        return self._stripe_account_id or None

    def create_payment_link_one_time(
        self,
        link_id: str,
        title: str,
        description: str | None,
        amount: int,
        base_amount: int,
        currency: str,
        require_fields: list[str],
        *,
        service_fee: int = 0,
    ) -> dict[str, Any]:
        principal = self._ensure_principal()
        metadata = {
            "user_id": principal.user_id,
            "user_email": principal.email or "",
            "link_id": link_id,
            "link_type": "one_time",
            "account_type": "connected_account",
            "base_amount": str(base_amount),
        }
        product_data: dict[str, Any] = {"name": product_name(title, "one_time")}
        if description:
            product_data["description"] = description
        payload: dict[str, Any] = {
            "line_items": [
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": product_data,
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                }
            ],
            "payment_intent_data": {"metadata": metadata},
            "metadata": metadata,
            "application_fee_amount": service_fee,
        }
        apply_require_fields_to_payload(payload, require_fields, recurring=False)
        stripe.api_key = settings.stripe_secret
        payment_link = stripe.PaymentLink.create(**payload, stripe_account=self._stripe_account_id)
        return {"id": payment_link.id, "url": payment_link.url}

    def create_payment_link_subscription(
        self,
        link_id: str,
        title: str,
        description: str | None,
        amount: int,
        base_amount: int,
        currency: str,
        interval: str,
        require_fields: list[str],
        *,
        service_fee_percent: float = 0.0,
    ) -> dict[str, Any]:
        principal = self._ensure_principal()
        metadata = {
            "user_id": principal.user_id,
            "user_email": principal.email or "",
            "link_id": link_id,
            "link_type": "subscription",
            "account_type": "connected_account",
            "base_amount": str(base_amount),
        }
        product_data: dict[str, Any] = {"name": product_name(title, "subscription")}
        if description:
            product_data["description"] = description
        payload: dict[str, Any] = {
            "line_items": [
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": product_data,
                        "unit_amount": amount,
                        "recurring": {"interval": interval},
                    },
                    "quantity": 1,
                }
            ],
            "subscription_data": {"metadata": metadata},
            "metadata": metadata,
            "application_fee_percent": service_fee_percent,
        }
        apply_require_fields_to_payload(payload, require_fields, recurring=True)
        stripe.api_key = settings.stripe_secret
        payment_link = stripe.PaymentLink.create(**payload, stripe_account=self._stripe_account_id)
        return {"id": payment_link.id, "url": payment_link.url}

    def disable_payment_link(self, payment_link_id: str) -> None:
        stripe.api_key = settings.stripe_secret
        stripe.PaymentLink.modify(payment_link_id, active=False, stripe_account=self._stripe_account_id)

    def list_transactions_for_link(
        self,
        user_id: str,
        link_id: str,
        limit: int = 100,
    ) -> dict[str, Any]:
        stripe.api_key = settings.stripe_secret
        query = f"metadata['user_id']:'{user_id}' AND metadata['link_id']:'{link_id}'"
        return stripe.PaymentIntent.search(
            query=query,
            limit=limit,
            expand=["data.charges.data.refunds"],
            stripe_account=self._stripe_account_id,
        )
