"""
E2E tests that call the real Stripe API (test mode).

Not run by default (excluded via pytest -m 'not e2e_stripe' in addopts).
Run explicitly: pytest -m e2e_stripe -v
Requires STRIPE_SECRET in .env (pydantic-settings reads it as stripe_secret).
"""

from __future__ import annotations

import pytest
import stripe

from payme.core.auth import Principal
from payme.db.repositories import StripeAccountRecord
from payme.services.payment_links import StripePaymentLinkFactory
from payme.services.stripe_platform_account_service import StripePlatformAccountService


def _e2e_principal(account_id: str = "acct_e2e_placeholder", status: str = "NEW") -> Principal:
    return Principal(
        user_id="e2e-user-id",
        email="e2e-test@example.com",
        external_sub="e2e-ext",
        stripe_account=StripeAccountRecord(
            user_id="e2e-user-id",
            stripe_account_id=account_id,
            country="GB",
            created_at="",
            status=status,
        ),
    )


@pytest.mark.e2e_stripe
class TestStripeE2E:
    """Create Connect account and payment link in Stripe, assert, clean up."""

    def test_connect_account_and_payment_link_created_in_stripe(self):
        """Create Connect account and platform-held payment link via StripePlatformAccountService + factory (NEW -> platform), verify, then clean up."""
        account_id = StripePlatformAccountService.create_custom_connected_account(email="e2e-test@example.com", country="GB")
        assert account_id.startswith("acct_")

        principal = _e2e_principal(account_id)  # status NEW -> factory returns platform link service
        platform = StripePaymentLinkFactory.get_link_service(principal)
        payment_link_id: str | None = None

        try:
            account = stripe.Account.retrieve(account_id)
            assert account.id == account_id
            assert account.type == "express"
            assert account.country.upper() == "GB"

            result = platform.create_payment_link_one_time(
                link_id="e2e-link-id",
                title="E2E Test",
                description=None,
                amount=100,
                currency="gbp",
                require_fields=["email"],
            )
            payment_link_id = result["id"]
            assert result["url"].startswith("https://")
            assert payment_link_id.startswith("plink_")

            link = stripe.PaymentLink.retrieve(payment_link_id)
            assert link.id == payment_link_id
            assert link.active is True
            assert link.metadata.get("user_id") == "e2e-user-id"
            assert link.metadata.get("link_id") == "e2e-link-id"
        finally:
            if payment_link_id:
                try:
                    platform.disable_payment_link(payment_link_id)
                    pl = stripe.PaymentLink.retrieve(payment_link_id)
                    assert pl.active is False
                except stripe.error.StripeError:
                    pass
            if account_id:
                try:
                    stripe.Account.delete(account_id)
                except stripe.error.StripeError:
                    pass

    def test_subscription_link_created_in_stripe(self):
        """Create subscription payment link on platform via factory (NEW -> platform), verify via Stripe API, then clean up."""
        platform = StripePaymentLinkFactory.get_link_service(_e2e_principal())
        payment_link_id: str | None = None

        try:
            result = platform.create_payment_link_subscription(
                link_id="e2e-sub-link-id",
                title="E2E Subscription",
                description=None,
                amount=500,
                currency="gbp",
                interval="month",
                require_fields=["email"],
            )
            payment_link_id = result["id"]
            assert result["url"].startswith("https://")
            assert payment_link_id.startswith("plink_")

            link = stripe.PaymentLink.retrieve(payment_link_id)
            assert link.id == payment_link_id
            assert link.active is True
            assert link.metadata.get("user_id") == "e2e-user-id"
            assert link.metadata.get("link_id") == "e2e-sub-link-id"
            assert link.metadata.get("link_type") == "subscription"

            line_items = stripe.PaymentLink.list_line_items(payment_link_id, limit=1)
            assert len(line_items.data) == 1
            first = line_items.data[0]
            price = first.price
            if isinstance(price, str):
                price = stripe.Price.retrieve(price)
            assert price.recurring.interval == "month"
            assert price.unit_amount == 500
        finally:
            if payment_link_id:
                try:
                    platform.disable_payment_link(payment_link_id)
                    pl = stripe.PaymentLink.retrieve(payment_link_id)
                    assert pl.active is False
                except stripe.error.StripeError:
                    pass
