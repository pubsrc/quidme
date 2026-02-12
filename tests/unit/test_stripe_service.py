"""Unit tests for Stripe platform account service and payment link services."""

from types import SimpleNamespace

import payme.services.stripe_platform_account_service as platform_module
import payme.services.payment_links.connected_link_service as link_module
from payme.core.constants import StripeAccountStatus
from payme.db.repositories import StripeAccountRecord
from payme.services.payment_links import StripeConnectedAccountLinkService
from payme.services.stripe_platform_account_service import StripePlatformAccountService

_TEST_ACCOUNT_ID = "acct_123"
_TEST_USER_ID = "user-1"


def _test_principal():
    from payme.core.auth import Principal
    return Principal(
        user_id=_TEST_USER_ID,
        email="test@example.com",
        external_sub="ext-1",
        stripe_account=StripeAccountRecord(
            user_id=_TEST_USER_ID,
            stripe_account_id=_TEST_ACCOUNT_ID,
            country="GB",
            created_at="",
            status=StripeAccountStatus.VERIFIED,
        ),
    )


def test_from_account_id_requires_valid_account_id():
    import pytest
    with pytest.raises(ValueError, match="stripe_account_id"):
        StripeConnectedAccountLinkService.from_account_id("")
    with pytest.raises(ValueError, match="acct_"):
        StripeConnectedAccountLinkService.from_account_id("invalid")


def test_platform_create_connected_account(monkeypatch):
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id="acct_1")

    monkeypatch.setattr(platform_module.stripe.Account, "create", staticmethod(fake_create))

    account_id = StripePlatformAccountService.create_custom_connected_account(email="test@example.com", country="GB")

    assert account_id == "acct_1"
    assert captured["type"] == "express"
    assert captured["email"] == "test@example.com"
    assert captured["country"] == "GB"


def test_platform_get_account_status(monkeypatch):
    monkeypatch.setattr(
        platform_module.stripe.Account,
        "retrieve",
        staticmethod(
            lambda id=None, **kwargs: {
                "charges_enabled": True,
                "payouts_enabled": False,
                "details_submitted": True,
                "requirements": {"currently_due": []},
                "capabilities": {"transfers": "active"},
            }
        ),
    )
    monkeypatch.setattr(
        platform_module.stripe.Balance,
        "retrieve",
        staticmethod(
            lambda stripe_account: {
                "pending": [{"amount": 100, "currency": "gbp"}],
                "available": [{"amount": 50, "currency": "gbp"}],
            }
        ),
    )

    status = StripePlatformAccountService.get_account_status(_TEST_ACCOUNT_ID)

    assert status["charges_enabled"] is True
    assert status["payouts_enabled"] is False
    assert status["transfers_enabled"] is True
    assert status["has_pending_balance"] is True
    assert status["pending_amount"] == 150
    assert status["pending_currency"] == "gbp"


def test_platform_create_account_link_uses_stripe(monkeypatch):
    def fake_create(**kwargs):
        return SimpleNamespace(url="https://stripe.example.com/onboard")

    monkeypatch.setattr(platform_module.stripe.AccountLink, "create", staticmethod(fake_create))

    url = StripePlatformAccountService.create_account_link(_TEST_ACCOUNT_ID)

    assert url == "https://stripe.example.com/onboard"


def test_connected_account_create_payment_link_one_time_with_fee(monkeypatch):
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id="plink_connected", url="https://example.com")

    monkeypatch.setattr(link_module.stripe.PaymentLink, "create", fake_create)

    service = StripeConnectedAccountLinkService(_test_principal())
    service.create_payment_link_one_time(
        link_id="link-1",
        title="Pay",
        description=None,
        amount=100,
        currency="gbp",
        require_fields=[],
        service_fee=10,
    )

    assert captured.get("stripe_account") == _TEST_ACCOUNT_ID
    assert captured.get("application_fee_amount") == 10
    assert captured["metadata"]["user_id"] == _TEST_USER_ID


def test_connected_account_disable_payment_link(monkeypatch):
    captured = {}

    def fake_modify(link_id, **kwargs):
        captured["link_id"] = link_id
        captured.update(kwargs)

    monkeypatch.setattr(link_module.stripe.PaymentLink, "modify", fake_modify)

    service = StripeConnectedAccountLinkService(_test_principal())
    service.disable_payment_link("plink_1")

    assert captured["link_id"] == "plink_1"
    assert captured["active"] is False
    assert captured.get("stripe_account") == _TEST_ACCOUNT_ID


def test_platform_disable_payment_link_static(monkeypatch):
    """StripePlatformAccountService.disable_platform_payment_link (e.g. used by expire_links handler)."""
    captured = {}

    def fake_modify(link_id, **kwargs):
        captured["link_id"] = link_id
        captured.update(kwargs)

    monkeypatch.setattr(platform_module.stripe.PaymentLink, "modify", staticmethod(fake_modify))

    StripePlatformAccountService.disable_platform_payment_link("plink_99")

    assert captured["link_id"] == "plink_99"
    assert captured["active"] is False


def test_from_account_id_disable_payment_link(monkeypatch):
    """StripeConnectedAccountLinkService.from_account_id(...).disable_payment_link (e.g. expire_links)."""
    captured = {}

    def fake_modify(link_id, **kwargs):
        captured["link_id"] = link_id
        captured.update(kwargs)

    monkeypatch.setattr(link_module.stripe.PaymentLink, "modify", fake_modify)

    service = StripeConnectedAccountLinkService.from_account_id(_TEST_ACCOUNT_ID)
    service.disable_payment_link("plink_1")

    assert captured["link_id"] == "plink_1"
    assert captured["active"] is False
    assert captured["stripe_account"] == _TEST_ACCOUNT_ID


def test_from_account_id_list_transactions_for_link(monkeypatch):
    captured = {}

    def fake_search(**kwargs):
        captured.update(kwargs)
        return {"data": []}

    monkeypatch.setattr(link_module.stripe.PaymentIntent, "search", fake_search)

    service = StripeConnectedAccountLinkService.from_account_id(_TEST_ACCOUNT_ID)
    resp = service.list_transactions_for_link(_TEST_USER_ID, "link-1", limit=50)

    assert resp == {"data": []}
    assert "metadata['user_id']:'user-1'" in captured["query"]
    assert "metadata['link_id']:'link-1'" in captured["query"]
    assert captured["limit"] == 50
    assert captured["stripe_account"] == _TEST_ACCOUNT_ID
