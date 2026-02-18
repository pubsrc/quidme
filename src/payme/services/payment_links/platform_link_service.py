"""Payment links created on the platform Stripe account (no application fee)."""

from __future__ import annotations

from typing import Any

import stripe

from payme.core.auth import Principal
from payme.core.settings import settings

from payme.services.payment_links.base import StripePaymentLinkService
from payme.services.payment_links.helpers import apply_require_fields_to_payload, product_name


class StripePlatformAccountLinkService(StripePaymentLinkService):
    """Creates payment links on the platform account (metadata only; no application fee)."""

    def __init__(self, principal: Principal) -> None:
        self._principal = principal

    @property
    def is_platform(self) -> bool:
        return True

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
        metadata = {
            "user_id": self._principal.user_id,
            "user_email": self._principal.email or "",
            "link_id": link_id,
            "link_type": "one_time",
            "account_type": "platform",
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
        }
        apply_require_fields_to_payload(payload, require_fields, recurring=False)
        stripe.api_key = settings.stripe_secret
        payment_link = stripe.PaymentLink.create(**payload)
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
        metadata = {
            "user_id": self._principal.user_id,
            "user_email": self._principal.email or "",
            "link_id": link_id,
            "link_type": "subscription",
            "account_type": "platform",
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
        }
        apply_require_fields_to_payload(payload, require_fields, recurring=True)
        stripe.api_key = settings.stripe_secret
        payment_link = stripe.PaymentLink.create(**payload)
        return {"id": payment_link.id, "url": payment_link.url}

    def disable_payment_link(self, payment_link_id: str) -> None:
        from payme.services.stripe_platform_account_service import StripePlatformAccountService
        StripePlatformAccountService.disable_platform_payment_link(payment_link_id)

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
        )
