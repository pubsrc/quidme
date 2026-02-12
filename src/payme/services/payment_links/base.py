"""Abstract base for Stripe payment link services (one-time and subscription)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StripePaymentLinkService(ABC):
    """
    Base for creating one-time and subscription payment links.
    Implementations create links either on the platform or on a connected account.
    """

    @abstractmethod
    def create_payment_link_one_time(
        self,
        link_id: str,
        title: str,
        description: str | None,
        amount: int,
        currency: str,
        require_fields: list[str],
        *,
        service_fee: int = 0,
    ) -> dict[str, Any]:
        """Create a one-time payment link. Returns dict with id and url."""
        ...

    @abstractmethod
    def create_payment_link_subscription(
        self,
        link_id: str,
        title: str,
        description: str | None,
        amount: int,
        currency: str,
        interval: str,
        require_fields: list[str],
        *,
        service_fee_percent: float = 0.0,
    ) -> dict[str, Any]:
        """Create a subscription (recurring) payment link. Returns dict with id and url."""
        ...

    @abstractmethod
    def disable_payment_link(self, payment_link_id: str) -> None:
        """Disable a payment link on the correct Stripe account."""
        ...

    @abstractmethod
    def list_transactions_for_link(
        self,
        user_id: str,
        link_id: str,
        limit: int = 100,
    ) -> dict[str, Any]:
        """List PaymentIntents for this link. Returns Stripe search result shape with data list."""
        ...

    @property
    @abstractmethod
    def is_platform(self) -> bool:
        """True if links are on the platform account; False if on a connected account."""
        ...

    @property
    def stripe_account_id(self) -> str | None:
        """Stripe Connect account id when is_platform is False; None for platform."""
        return None
