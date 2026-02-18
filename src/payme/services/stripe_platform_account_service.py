"""
Platform (admin) Stripe service: only the platform can create connected accounts,
create onboarding links for them, transfer funds, and manage platform-held payment links.

Connected accounts create payment links via payme.services.payment_links.StripeConnectedAccountLinkService.
"""

from __future__ import annotations

from typing import Any

import stripe

from payme.core.settings import settings


class StripePlatformAccountService:
    """
    Admin operations on Stripe Connect: create connected accounts, onboarding links,
    get connected account status, disable platform-held payment links.
    """

    @staticmethod
    def create_custom_connected_account(email: str, country: str) -> str:
        """Create a deferred Express Connect account. Returns Stripe account id."""
        stripe.api_key = settings.stripe_secret
        account = stripe.Account.create(
            email=email,
            type="express",
            country=country,
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
        )
        return account.id

    @staticmethod
    def create_account_link(stripe_account_id: str) -> str:
        """
        Generate Stripe onboarding link for a connected account (platform creates the link).
        Raises ValueError if the account is not connected to the platform.
        """
        stripe.api_key = settings.stripe_secret
        try:
            link = stripe.AccountLink.create(
                account=stripe_account_id,
                refresh_url=settings.payme_account_refresh_url,
                return_url=settings.payme_account_return_url,
                type="account_onboarding",
            )
            return link.url
        except stripe.InvalidRequestError as e:
            if "not connected" in str(e).lower() or "does not exist" in str(e).lower():
                raise ValueError(
                    "Stripe account is not connected to this platform or no longer exists. "
                    "Complete Connect setup from the start page, or try again later."
                ) from e
            raise

    @staticmethod
    def get_account_status(stripe_account_id: str) -> dict[str, Any]:
        """Return charges_enabled, payouts_enabled, balance, etc. for a connected account."""
        stripe.api_key = settings.stripe_secret
        account = stripe.Account.retrieve(stripe_account_id)
        balance = stripe.Balance.retrieve(stripe_account=stripe_account_id)
        pending = balance.get("pending", []) or []
        available = balance.get("available", []) or []
        pending_total = sum(item.get("amount", 0) for item in pending)
        available_total = sum(item.get("amount", 0) for item in available)
        pending_amount = pending_total + available_total
        currency = None
        if available:
            currency = available[0].get("currency")
        elif pending:
            currency = pending[0].get("currency")
        return {
            "charges_enabled": account.get("charges_enabled", False),
            "payouts_enabled": account.get("payouts_enabled", False),
            "details_submitted": account.get("details_submitted", False),
            "requirements_due": account.get("requirements", {}).get("currently_due", []),
            "transfers_enabled": account.get("capabilities", {}).get("transfers") == "active",
            "has_pending_balance": pending_amount > 0,
            "pending_amount": pending_amount,
            "pending_currency": currency,
        }

    @staticmethod
    def disable_platform_payment_link(payment_link_id: str) -> None:
        """Disable a payment link held on the platform account (e.g. expire_links, disable route)."""
        stripe.api_key = settings.stripe_secret
        stripe.PaymentLink.modify(payment_link_id, active=False)

    @staticmethod
    def delete_connected_account(stripe_account_id: str) -> None:
        """
        Delete a Connect account. Call with platform secret key.
        Idempotent: if account is already deleted, Stripe may raise; caller can catch and ignore.
        """
        stripe.api_key = settings.stripe_secret
        stripe.Account.delete(stripe_account_id)

    @staticmethod
    def create_transfer(amount: int, currency: str, destination: str) -> str:
        """Create a Stripe transfer from platform balance to a connected account."""
        stripe.api_key = settings.stripe_secret
        transfer = stripe.Transfer.create(
            amount=amount,
            currency=currency,
            destination=destination,
        )
        return transfer.id
