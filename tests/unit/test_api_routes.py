"""Unit tests for API routes using TestClient and dependency overrides."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import stripe
from fastapi.testclient import TestClient

from payme.api.dependencies import (
    get_stripe_connected_account_link_service_optional,
    get_stripe_platform_account_link_service,
)
from payme.api.main import app
from payme.api.utils import normalize_expiry_date, stripe_error_message
from payme.core.auth import Principal
from payme.models.payment import PaymentLinkCreate, RefundRequest, SubscriptionCreate


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeUserRecord:
    def __init__(self, user_id: str, email: str | None, stripe_account_id: str | None):
        self.user_id = user_id
        self.email = email
        self.stripe_account_id = stripe_account_id


class FakeUsersRepo:
    def __init__(self, record: FakeUserRecord | None):
        self._record = record
        self.updated = None

    def get(self, user_id: str) -> FakeUserRecord | None:
        return self._record

    def update_stripe_account(self, user_id: str, stripe_account_id: str) -> None:
        self.updated = stripe_account_id
        if self._record:
            self._record.stripe_account_id = stripe_account_id


class FakeStripeAccountRecord:
    def __init__(
        self,
        user_id: str,
        stripe_account_id: str,
        country: str = "GB",
        status: str = "NEW",
        created_at: str = "2025-01-01T00:00:00+00:00",
    ):
        self.user_id = user_id
        self.stripe_account_id = stripe_account_id
        self.country = country
        self.status = status
        self.created_at = created_at


class FakeStripeAccountsRepo:
    def __init__(self, account: FakeStripeAccountRecord | None, create_raises: bool = False):
        self._account = account
        self.create_raises = create_raises
        self.created: list[dict] = []

    def get_primary_for_user(self, user_id: str) -> FakeStripeAccountRecord | None:
        return self._account

    def create(self, user_id: str, stripe_account_id: str | None, country: str) -> None:
        if self.create_raises:
            raise RuntimeError("ddb error")
        self.created.append({"user_id": user_id, "stripe_account_id": stripe_account_id, "country": country})


class FakeLinksRepo:
    def __init__(self, item: dict | None = None):
        self.created: list[dict] = []
        self._item = item
        self.disabled: list[str] = []
        self.list_by_user_items: list[dict] = []

    def create_draft(self, **kwargs: Any) -> str:
        self.created.append(kwargs)
        return kwargs["link_id"]

    def update_with_stripe(
        self,
        link_id: str,
        stripe_payment_link_id: str,
        url: str,
        service_fee: int,
        on_platform: bool = False,
    ) -> None:
        pass

    def create(self, **kwargs: Any) -> str:
        self.created.append(kwargs)
        return kwargs["link_id"]

    def get(self, link_id: str) -> dict | None:
        return self._item

    def mark_disabled(self, link_id: str) -> None:
        self.disabled.append(link_id)

    def list_by_user(self, user_id: str, limit: int = 50) -> list[dict]:
        return self.list_by_user_items


class FakeSubsRepo:
    def __init__(self, item: dict | None = None):
        self.created: list[dict] = []
        self._item = item
        self.disabled: list[str] = []
        self.list_by_user_items: list[dict] = []

    def create_draft(self, **kwargs: Any) -> str:
        self.created.append(kwargs)
        return kwargs["subscription_id"]

    def update_with_stripe(
        self,
        subscription_id: str,
        stripe_payment_link_id: str,
        url: str,
        service_fee: int,
        on_platform: bool = False,
    ) -> None:
        pass

    def create(self, **kwargs: Any) -> str:
        self.created.append(kwargs)
        return kwargs["subscription_id"]

    def get(self, subscription_id: str) -> dict | None:
        return self._item

    def mark_disabled(self, subscription_id: str) -> None:
        self.disabled.append(subscription_id)

    def list_by_user(self, user_id: str, limit: int = 50) -> list[dict]:
        return self.list_by_user_items


class FakeLinkService:
    """Fake for StripePaymentLinkService (factory-returned link service)."""

    def __init__(self, is_platform: bool = True, created_one_time: list | None = None, created_subscription: list | None = None):
        self._is_platform = is_platform
        self.created_one_time = created_one_time if created_one_time is not None else []
        self.created_subscription = created_subscription if created_subscription is not None else []
        self.disabled: list[str] = []

    @property
    def is_platform(self) -> bool:
        return self._is_platform

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
    ) -> dict:
        self.created_one_time.append({"link_id": link_id, "title": title, "amount": amount, "service_fee": service_fee})
        return {"id": "plink_1", "url": "https://example.com"}

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
    ) -> dict:
        self.created_subscription.append({"link_id": link_id, "amount": amount})
        return {"id": "plink_2", "url": "https://example.com"}

    def disable_payment_link(self, payment_link_id: str) -> None:
        self.disabled.append(payment_link_id)

    def list_transactions_for_link(self, user_id: str, link_id: str, limit: int = 100) -> dict:
        return {"data": []}


class FakeStripeConnectedAccountLinkService:
    """Fake for StripeConnectedAccountLinkService (list_transactions_for_link on connected links)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.disabled: list[str] = []

    def disable_payment_link(self, payment_link_id: str) -> None:
        self.disabled.append(payment_link_id)

    def list_transactions_for_link(self, user_id: str, link_id: str, limit: int = 100) -> dict:
        return {"data": []}

    @property
    def is_platform(self) -> bool:
        return False


class FakeStripePlatformAccountLinkService:
    """Fake for platform link service (list_transactions_for_link on platform-held links)."""

    def list_transactions_for_link(self, user_id: str, link_id: str, limit: int = 100) -> dict:
        return {"data": []}

    @property
    def is_platform(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Test client with auth override
# ---------------------------------------------------------------------------

# Principal with Stripe account (for routes that need require_principal() - status must be VERIFIED or RESTRICTED)
def _principal_with_account() -> Principal:
    return Principal(
        user_id="user-1",
        email="test@example.com",
        external_sub="sub-cognito",
        stripe_account=FakeStripeAccountRecord("user-1", "acct_123", status="VERIFIED"),
    )


def _principal_without_account() -> Principal:
    return Principal(
        user_id="user-1",
        email="test@example.com",
        external_sub="sub-cognito",
        stripe_account=None,
    )


def override_get_resolved_principal() -> Principal:
    return _principal_with_account()


# ---------------------------------------------------------------------------
# Utils / helpers
# ---------------------------------------------------------------------------


def test_normalize_expiry_date() -> None:
    assert normalize_expiry_date(None) is None
    value = normalize_expiry_date(date(2030, 1, 1))
    assert value is not None
    assert value.hour == 23 and value.minute == 59 and value.second == 59


def test_stripe_error_message_prefers_user_message() -> None:
    exc = MagicMock(spec=stripe.error.StripeError, user_message="user message", error=None)
    assert stripe_error_message(exc) == "user message"


def test_stripe_error_message_falls_back_to_error_message() -> None:
    err = MagicMock(message="boom")
    exc = MagicMock(spec=stripe.error.StripeError, user_message=None, error=err)
    assert stripe_error_message(exc) == "boom"


def test_stripe_error_message_falls_back_to_str() -> None:
    class Dummy:
        user_message = None
        error = None

        def __str__(self) -> str:
            return "fallback"

    assert stripe_error_message(Dummy()) == "fallback"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health() -> None:
    client = TestClient(app)
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Accounts (connect, status, onboarding)
# ---------------------------------------------------------------------------


def test_connect_account_uses_override(monkeypatch: Any) -> None:
    from payme.api import dependencies as deps

    class FakePlatformService:
        @staticmethod
        def create_custom_connected_account(email: str, country: str) -> str:
            return "acct_fake"

    users_repo = FakeUsersRepo(FakeUserRecord("user-1", "test@example.com", None))
    accounts_repo = FakeStripeAccountsRepo(None)

    app.dependency_overrides[deps.get_resolved_principal] = lambda: _principal_without_account()
    app.dependency_overrides[deps.get_users_repository] = lambda: users_repo
    app.dependency_overrides[deps.get_stripe_accounts_repository] = lambda: accounts_repo
    app.dependency_overrides[deps.get_stripe_platform_account_service] = lambda: FakePlatformService

    client = TestClient(app)
    r = client.post(
        "/api/v1/platform/connected-accounts",
        headers={"Authorization": "Bearer x"},
        json={"country": "GB"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 200
    assert r.json()["stripe_account_id"] == "acct_fake"
    assert users_repo.updated == "acct_fake"
    assert len(accounts_repo.created) == 1
    assert accounts_repo.created[0]["user_id"] == "user-1"
    assert accounts_repo.created[0]["stripe_account_id"] == "acct_fake"


def test_connect_account_missing_email_returns_400(monkeypatch: Any) -> None:
    from payme.api import dependencies as deps

    principal_no_email = Principal(
        user_id="user-1",
        email=None,
        external_sub="sub-cognito",
        stripe_account=None,
    )
    users_repo = FakeUsersRepo(None)
    accounts_repo = FakeStripeAccountsRepo(None)
    app.dependency_overrides[deps.get_resolved_principal] = lambda: principal_no_email
    app.dependency_overrides[deps.get_users_repository] = lambda: users_repo
    app.dependency_overrides[deps.get_stripe_accounts_repository] = lambda: accounts_repo

    client = TestClient(app)
    r = client.post(
        "/api/v1/platform/connected-accounts",
        headers={"Authorization": "Bearer x"},
        json={"country": "GB"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 400
    assert "email" in r.json()["detail"].lower()


def test_connect_account_returns_existing_account(monkeypatch: Any) -> None:
    from payme.api import dependencies as deps

    principal_existing = Principal(
        user_id="user-1",
        email="test@example.com",
        external_sub="sub-cognito",
        stripe_account=FakeStripeAccountRecord("user-1", "acct_existing"),
    )
    app.dependency_overrides[deps.get_resolved_principal] = lambda: principal_existing

    client = TestClient(app)
    r = client.post(
        "/api/v1/platform/connected-accounts",
        headers={"Authorization": "Bearer x"},
        json={"country": "GB"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 200
    assert r.json()["stripe_account_id"] == "acct_existing"


def test_create_onboarding_link_requires_account(monkeypatch: Any) -> None:
    """Onboarding link requires Stripe account; returns 403 when none."""
    from payme.api import dependencies as deps

    app.dependency_overrides[deps.get_resolved_principal] = lambda: _principal_without_account()

    client = TestClient(app)
    r = client.post("/api/v1/accounts/onboarding", headers={"Authorization": "Bearer x"})
    app.dependency_overrides.clear()
    assert r.status_code == 403
    # 403 Stripe account required: app returns payload as body (no "detail" wrapper)
    body = r.json()
    msg = (body.get("message") or str(body.get("detail", "")) or "").lower()
    assert "setup" in msg or "complete" in msg


def test_create_onboarding_link_success(monkeypatch: Any) -> None:
    from payme.api import dependencies as deps

    class FakePlatformServiceWithOnboarding:
        @staticmethod
        def create_account_link(stripe_account_id: str) -> str:
            return "https://stripe.example.com/onboard"

    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_stripe_platform_account_service] = lambda: FakePlatformServiceWithOnboarding

    client = TestClient(app)
    r = client.post("/api/v1/accounts/onboarding", headers={"Authorization": "Bearer x"})
    app.dependency_overrides.clear()
    assert r.status_code == 200
    assert "onboarding_url" in r.json()
    assert "stripe.example.com" in r.json()["onboarding_url"]


def test_delete_account_deletes_user_data_and_cognito(monkeypatch: Any) -> None:
    """DELETE /accounts/account deletes DynamoDB data (except user_identities), Stripe account, and Cognito user."""
    from unittest.mock import MagicMock

    from payme.api import dependencies as deps

    principal = Principal(
        user_id="user-del",
        email="del@example.com",
        external_sub="cognito-sub-123",
        stripe_account=FakeStripeAccountRecord("user-del", "acct_xyz", status="VERIFIED"),
    )
    users_repo = MagicMock(spec=["delete"])
    stripe_accounts_repo = MagicMock(spec=["delete"])
    payment_links_repo = MagicMock(spec=["delete_all_for_user"])
    subscriptions_repo = MagicMock(spec=["delete_all_for_user"])
    stripe_subscriptions_repo = MagicMock(spec=["delete_all_for_user"])
    transactions_repo = MagicMock(spec=["delete_all_for_user"])
    platform_service_class = MagicMock()
    cognito_delete_user = MagicMock()

    app.dependency_overrides[deps.get_resolved_principal] = lambda: principal
    app.dependency_overrides[deps.get_users_repository] = lambda: users_repo
    app.dependency_overrides[deps.get_stripe_accounts_repository] = lambda: stripe_accounts_repo
    app.dependency_overrides[deps.get_payment_links_repository] = lambda: payment_links_repo
    app.dependency_overrides[deps.get_subscriptions_repository] = lambda: subscriptions_repo
    app.dependency_overrides[deps.get_stripe_subscriptions_repository] = lambda: stripe_subscriptions_repo
    app.dependency_overrides[deps.get_transactions_repository] = lambda: transactions_repo
    app.dependency_overrides[deps.get_stripe_platform_account_service] = lambda: platform_service_class
    monkeypatch.setattr(
        "payme.api.v1.routes.accounts.cognito_delete_user",
        cognito_delete_user,
    )

    client = TestClient(app)
    r = client.delete("/api/v1/accounts/account", headers={"Authorization": "Bearer x"})

    app.dependency_overrides.clear()
    assert r.status_code == 204
    platform_service_class.delete_connected_account.assert_called_once_with("acct_xyz")
    transactions_repo.delete_all_for_user.assert_called_once_with("user-del")
    payment_links_repo.delete_all_for_user.assert_called_once_with("user-del")
    subscriptions_repo.delete_all_for_user.assert_called_once_with("user-del")
    stripe_subscriptions_repo.delete_all_for_user.assert_called_once_with("user-del")
    stripe_accounts_repo.delete.assert_called_once_with("user-del")
    users_repo.delete.assert_called_once_with("user-del")
    cognito_delete_user.assert_called_once_with("cognito-sub-123")


def test_delete_account_no_stripe_account_skips_stripe_delete(monkeypatch: Any) -> None:
    """When user has no Stripe account, delete_account does not call Stripe."""
    from unittest.mock import MagicMock

    from payme.api import dependencies as deps

    principal = Principal(
        user_id="user-no-acct",
        email="n@example.com",
        external_sub="sub-456",
        stripe_account=None,
    )
    users_repo = MagicMock(spec=["delete"])
    stripe_accounts_repo = MagicMock(spec=["delete"])
    payment_links_repo = MagicMock(spec=["delete_all_for_user"])
    subscriptions_repo = MagicMock(spec=["delete_all_for_user"])
    stripe_subscriptions_repo = MagicMock(spec=["delete_all_for_user"])
    transactions_repo = MagicMock(spec=["delete_all_for_user"])
    platform_service_class = MagicMock()
    cognito_delete_user = MagicMock()

    app.dependency_overrides[deps.get_resolved_principal] = lambda: principal
    app.dependency_overrides[deps.get_users_repository] = lambda: users_repo
    app.dependency_overrides[deps.get_stripe_accounts_repository] = lambda: stripe_accounts_repo
    app.dependency_overrides[deps.get_payment_links_repository] = lambda: payment_links_repo
    app.dependency_overrides[deps.get_subscriptions_repository] = lambda: subscriptions_repo
    app.dependency_overrides[deps.get_stripe_subscriptions_repository] = lambda: stripe_subscriptions_repo
    app.dependency_overrides[deps.get_transactions_repository] = lambda: transactions_repo
    app.dependency_overrides[deps.get_stripe_platform_account_service] = lambda: platform_service_class
    monkeypatch.setattr(
        "payme.api.v1.routes.accounts.cognito_delete_user",
        cognito_delete_user,
    )

    client = TestClient(app)
    r = client.delete("/api/v1/accounts/account", headers={"Authorization": "Bearer x"})

    app.dependency_overrides.clear()
    assert r.status_code == 204
    platform_service_class.delete_connected_account.assert_not_called()
    cognito_delete_user.assert_called_once_with("sub-456")


# ---------------------------------------------------------------------------
# Payment links (get_principal)
# ---------------------------------------------------------------------------


def test_create_payment_link_success_no_account_uses_platform(monkeypatch: Any) -> None:
    """Creating payment link with RESTRICTED (non-VERIFIED) account uses platform link service and returns 200."""
    from payme.api import dependencies as deps

    links_repo = FakeLinksRepo()
    link_fake = FakeLinkService(is_platform=True)

    def principal_restricted() -> Principal:
        return Principal(
            user_id="user-1",
            email="test@example.com",
            external_sub="sub-cognito",
            stripe_account=FakeStripeAccountRecord("user-1", "acct_123", status="RESTRICTED"),
        )

    app.dependency_overrides[deps.get_resolved_principal] = principal_restricted
    app.dependency_overrides[deps.get_payment_links_repository] = lambda: links_repo
    app.dependency_overrides[deps.get_stripe_link_service] = lambda: link_fake

    client = TestClient(app)
    r = client.post(
        "/api/v1/payment-links",
        headers={"Authorization": "Bearer x"},
        json={"amount": 100, "currency": "gbp"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 200
    assert r.json()["amount"] == 100
    assert len(link_fake.created_one_time) == 1
    assert link_fake.created_one_time[0]["amount"] == 158  # total = (100+50)/0.95


def test_create_payment_link_success(monkeypatch: Any) -> None:
    from payme.api import dependencies as deps

    links_repo = FakeLinksRepo()
    link_fake = FakeLinkService(is_platform=False)  # connected account path

    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_payment_links_repository] = lambda: links_repo
    app.dependency_overrides[deps.get_stripe_link_service] = lambda: link_fake

    client = TestClient(app)
    r = client.post(
        "/api/v1/payment-links",
        headers={"Authorization": "Bearer x"},
        json={"amount": 100, "currency": "gbp"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 200, r.json()
    data = r.json()
    assert data["service_fee"] == 8  # 5% of total (158)
    assert data["amount"] == 100
    assert len(links_repo.created) >= 1
    assert len(link_fake.created_one_time) == 1
    assert link_fake.created_one_time[0]["amount"] == 158  # total with fixed_fee + percent fees


def test_create_payment_link_title_optional(monkeypatch: Any) -> None:
    from payme.api import dependencies as deps

    links_repo = FakeLinksRepo()
    link_fake = FakeLinkService(is_platform=False)

    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_payment_links_repository] = lambda: links_repo
    app.dependency_overrides[deps.get_stripe_link_service] = lambda: link_fake

    client = TestClient(app)
    r = client.post(
        "/api/v1/payment-links",
        headers={"Authorization": "Bearer x"},
        json={"amount": 100, "currency": "gbp", "title": "  Test  "},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 200
    assert r.json()["title"] == "Test"
    assert len(link_fake.created_one_time) == 1
    assert link_fake.created_one_time[0]["title"] == "Test"


def test_create_quick_payment_link_success_without_dynamo(monkeypatch: Any) -> None:
    from payme.api import dependencies as deps

    link_fake = FakeLinkService(is_platform=False)

    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_stripe_link_service] = lambda: link_fake

    client = TestClient(app)
    r = client.post(
        "/api/v1/payment-links/quick-payments",
        headers={"Authorization": "Bearer x"},
        json={"title": "Quick Piano Payment", "amount": 100, "currency": "bgn"},
    )
    app.dependency_overrides.clear()

    assert r.status_code == 200, r.json()
    assert r.json()["url"] == "https://example.com"
    assert len(link_fake.created_one_time) == 1
    assert link_fake.created_one_time[0]["title"] == "Quick Piano Payment"
    assert link_fake.created_one_time[0]["amount"] == 158  # total with fixed + percent fees


def test_list_payment_links_sorted(monkeypatch: Any) -> None:
    from payme.api import dependencies as deps

    links_repo = FakeLinksRepo()
    links_repo.list_by_user_items = [
        {
            "link_id": "link-1",
            "user_id": "user-1",
            "stripe_payment_link_id": "plink_1",
            "url": "https://example.com/1",
            "title": "Old",
            "amount": 100,
            "service_fee": 55,
            "currency": "gbp",
            "status": "ACTIVE",
            "created_at": "2024-01-01T00:00:00+00:00",
        },
        {
            "link_id": "link-2",
            "user_id": "user-1",
            "stripe_payment_link_id": "plink_2",
            "url": "https://example.com/2",
            "title": "New",
            "amount": 200,
            "service_fee": 60,
            "currency": "gbp",
            "status": "ACTIVE",
            "created_at": "2024-02-01T00:00:00+00:00",
        },
    ]
    connected_fake = FakeStripeConnectedAccountLinkService()
    platform_fake = FakeStripePlatformAccountLinkService()
    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_payment_links_repository] = lambda: links_repo
    app.dependency_overrides[deps.get_stripe_platform_account_link_service] = lambda: platform_fake
    app.dependency_overrides[get_stripe_connected_account_link_service_optional] = lambda: connected_fake

    client = TestClient(app)
    r = client.get("/api/v1/payment-links", headers={"Authorization": "Bearer x"})
    app.dependency_overrides.clear()
    assert r.status_code == 200
    items = r.json()
    assert items[0]["title"] == "New"


def test_disable_payment_link(monkeypatch: Any) -> None:
    from payme.api import dependencies as deps

    links_repo = FakeLinksRepo(
        item={
            "link_id": "link-1",
            "user_id": "user-1",
            "stripe_payment_link_id": "plink_1",
            "on_platform": False,
        }
    )
    link_fake = FakeLinkService()

    class FakeStripePlatformAccountServiceClass:
        @staticmethod
        def disable_platform_payment_link(link_id: str) -> None:
            pass

    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_payment_links_repository] = lambda: links_repo
    app.dependency_overrides[deps.get_stripe_platform_account_service] = lambda: FakeStripePlatformAccountServiceClass
    app.dependency_overrides[deps.get_stripe_link_service] = lambda: link_fake

    client = TestClient(app)
    r = client.post("/api/v1/payment-links/link-1/disable", headers={"Authorization": "Bearer x"})
    app.dependency_overrides.clear()
    assert r.status_code == 200
    assert r.json()["status"] == "DISABLED"
    assert "link-1" in links_repo.disabled
    assert "plink_1" in link_fake.disabled


def test_disable_subscription_link_not_found(monkeypatch: Any) -> None:
    from payme.api import dependencies as deps

    subs_repo = FakeSubsRepo(item=None)

    class FakeStripePlatformAccountServiceClass:
        @staticmethod
        def disable_platform_payment_link(link_id: str) -> None:
            pass

    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_subscriptions_repository] = lambda: subs_repo
    app.dependency_overrides[deps.get_stripe_platform_account_service] = lambda: FakeStripePlatformAccountServiceClass
    app.dependency_overrides[deps.get_stripe_link_service] = lambda: FakeLinkService()

    client = TestClient(app)
    r = client.post("/api/v1/subscriptions/sub-1/disable", headers={"Authorization": "Bearer x"})
    app.dependency_overrides.clear()
    assert r.status_code == 404


def test_create_subscription_link_success(monkeypatch: Any) -> None:
    from payme.api import dependencies as deps

    subs_repo = FakeSubsRepo()
    link_fake = FakeLinkService(is_platform=False)
    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_subscriptions_repository] = lambda: subs_repo
    app.dependency_overrides[deps.get_stripe_link_service] = lambda: link_fake

    client = TestClient(app)
    r = client.post(
        "/api/v1/subscriptions",
        headers={"Authorization": "Bearer x"},
        json={"amount": 200, "currency": "usd", "interval": "month"},
    )
    app.dependency_overrides.clear()
    assert r.status_code == 200
    assert r.json()["service_fee"] == 13  # 5% of total (264) for amount 200
    assert len(subs_repo.created) >= 1
    assert len(link_fake.created_subscription) == 1


# ---------------------------------------------------------------------------
# Transfers
# ---------------------------------------------------------------------------


def test_transfer_pending_earnings_success() -> None:
    from payme.api import dependencies as deps

    class FakeTransferAccountsRepo:
        def __init__(self) -> None:
            self.cleared: list[list[str]] = []

        def get_pending_earnings(self, user_id: str) -> dict[str, int]:
            return {"gbp": 1050, "usd": 300}

        def clear_pending_earnings(self, user_id: str, only_currencies: list[str] | None = None) -> None:
            self.cleared.append(list(only_currencies or []))

    class FakePlatformService:
        calls: list[dict[str, Any]] = []

        @staticmethod
        def create_transfer(amount: int, currency: str, destination: str) -> str:
            FakePlatformService.calls.append(
                {"amount": amount, "currency": currency, "destination": destination}
            )
            return "tr_123"

    repo = FakeTransferAccountsRepo()
    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_stripe_accounts_repository] = lambda: repo
    app.dependency_overrides[deps.get_stripe_platform_account_service] = lambda: FakePlatformService

    client = TestClient(app)
    r = client.post("/api/v1/transfers/transfer", headers={"Authorization": "Bearer x"})
    app.dependency_overrides.clear()

    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["stripe_account_id"] == "acct_123"
    assert body["transferred"] == {"gbp": 1050, "usd": 300}
    assert body["failed"] == {}
    assert FakePlatformService.calls == [
        {"amount": 1050, "currency": "gbp", "destination": "acct_123"},
        {"amount": 300, "currency": "usd", "destination": "acct_123"},
    ]
    assert repo.cleared == [["gbp", "usd"]]


def test_transfer_pending_earnings_no_pending() -> None:
    from payme.api import dependencies as deps

    class FakeTransferAccountsRepo:
        def get_pending_earnings(self, user_id: str) -> dict[str, int]:
            return {}

        def clear_pending_earnings(self, user_id: str, only_currencies: list[str] | None = None) -> None:
            raise AssertionError("clear_pending_earnings should not be called")

    class FakePlatformService:
        @staticmethod
        def create_transfer(amount: int, currency: str, destination: str) -> str:
            raise AssertionError("create_transfer should not be called")

    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_stripe_accounts_repository] = lambda: FakeTransferAccountsRepo()
    app.dependency_overrides[deps.get_stripe_platform_account_service] = lambda: FakePlatformService

    client = TestClient(app)
    r = client.post("/api/v1/transfers/transfer", headers={"Authorization": "Bearer x"})
    app.dependency_overrides.clear()

    assert r.status_code == 200
    body = r.json()
    assert body["transferred"] == {}
    assert body["failed"] == {}
    assert "No pending earnings" in body["message"]


def test_transfer_pending_earnings_missing_connected_account_returns_400() -> None:
    from payme.api import dependencies as deps

    principal_missing_account_id = Principal(
        user_id="user-1",
        email="test@example.com",
        external_sub="sub-cognito",
        stripe_account=FakeStripeAccountRecord("user-1", "", status="VERIFIED"),
    )

    class FakeTransferAccountsRepo:
        def get_pending_earnings(self, user_id: str) -> dict[str, int]:
            return {"gbp": 100}

    app.dependency_overrides[deps.get_resolved_principal] = lambda: principal_missing_account_id
    app.dependency_overrides[deps.get_stripe_accounts_repository] = lambda: FakeTransferAccountsRepo()

    client = TestClient(app)
    r = client.post("/api/v1/transfers/transfer", headers={"Authorization": "Bearer x"})
    app.dependency_overrides.clear()

    assert r.status_code == 400
    assert "Connected Stripe account is required" in r.json()["detail"]


def test_transfer_pending_earnings_partial_failure() -> None:
    from payme.api import dependencies as deps

    class FakeTransferAccountsRepo:
        def __init__(self) -> None:
            self.cleared: list[list[str]] = []

        def get_pending_earnings(self, user_id: str) -> dict[str, int]:
            return {"gbp": 1000, "usd": 500}

        def clear_pending_earnings(self, user_id: str, only_currencies: list[str] | None = None) -> None:
            self.cleared.append(list(only_currencies or []))

    class FakePlatformService:
        @staticmethod
        def create_transfer(amount: int, currency: str, destination: str) -> str:
            if currency == "usd":
                raise RuntimeError("stripe transfer failed")
            return "tr_ok"

    repo = FakeTransferAccountsRepo()
    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_stripe_accounts_repository] = lambda: repo
    app.dependency_overrides[deps.get_stripe_platform_account_service] = lambda: FakePlatformService

    client = TestClient(app)
    r = client.post("/api/v1/transfers/transfer", headers={"Authorization": "Bearer x"})
    app.dependency_overrides.clear()

    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["transferred"] == {"gbp": 1000}
    assert "usd" in body["failed"]
    assert repo.cleared == [["gbp"]]


def test_create_payouts_success() -> None:
    from payme.api import dependencies as deps

    class FakePlatformService:
        @staticmethod
        def create_payouts_from_available_balance(stripe_account_id: str) -> dict[str, Any]:
            return {
                "transferred": {"gbp": 1000},
                "failed": {},
                "payout_ids": {"gbp": "po_123"},
            }

    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_stripe_platform_account_service] = lambda: FakePlatformService

    client = TestClient(app)
    r = client.post("/api/v1/transfers/payouts", headers={"Authorization": "Bearer x"})
    app.dependency_overrides.clear()

    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["stripe_account_id"] == "acct_123"
    assert body["transferred"] == {"gbp": 1000}
    assert body["failed"] == {}
    assert body["payout_ids"] == {"gbp": "po_123"}


def test_create_payouts_no_available_balance() -> None:
    from payme.api import dependencies as deps

    class FakePlatformService:
        @staticmethod
        def create_payouts_from_available_balance(stripe_account_id: str) -> dict[str, Any]:
            return {
                "transferred": {},
                "failed": {},
                "payout_ids": {},
            }

    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_stripe_platform_account_service] = lambda: FakePlatformService

    client = TestClient(app)
    r = client.post("/api/v1/transfers/payouts", headers={"Authorization": "Bearer x"})
    app.dependency_overrides.clear()

    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["transferred"] == {}
    assert body["failed"] == {}
    assert body["payout_ids"] == {}
    assert "No available balance" in body["message"]


def test_create_payouts_failure_returns_502() -> None:
    from payme.api import dependencies as deps

    class FakePlatformService:
        @staticmethod
        def create_payouts_from_available_balance(stripe_account_id: str) -> dict[str, Any]:
            return {
                "transferred": {},
                "failed": {"gbp": "payout failed"},
                "payout_ids": {},
            }

    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_stripe_platform_account_service] = lambda: FakePlatformService

    client = TestClient(app)
    r = client.post("/api/v1/transfers/payouts", headers={"Authorization": "Bearer x"})
    app.dependency_overrides.clear()

    assert r.status_code == 502
    body = r.json()["detail"]
    assert body["message"] == "Payout failed"
    assert "gbp" in body["failed"]


def test_create_payout_schedule_success_weekly() -> None:
    from payme.api import dependencies as deps

    class FakePlatformService:
        @staticmethod
        def update_payout_schedule(
            stripe_account_id: str,
            interval: str,
            weekly_anchor: str | None = None,
            monthly_anchor: int | None = None,
        ) -> dict[str, Any]:
            assert stripe_account_id == "acct_123"
            assert interval == "weekly"
            assert weekly_anchor == "monday"
            assert monthly_anchor is None
            return {"interval": "weekly", "weekly_anchor": "monday"}

    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_stripe_platform_account_service] = lambda: FakePlatformService

    client = TestClient(app)
    r = client.post(
        "/api/v1/transfers/schedules",
        headers={"Authorization": "Bearer x"},
        json={"interval": "weekly", "weekly_anchor": "monday"},
    )
    app.dependency_overrides.clear()

    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["stripe_account_id"] == "acct_123"
    assert body["schedule"] == {"interval": "weekly", "weekly_anchor": "monday"}


def test_create_payout_schedule_requires_anchor_for_weekly() -> None:
    from payme.api import dependencies as deps

    class FakePlatformService:
        @staticmethod
        def update_payout_schedule(
            stripe_account_id: str,
            interval: str,
            weekly_anchor: str | None = None,
            monthly_anchor: int | None = None,
        ) -> dict[str, Any]:
            return {"interval": interval}

    app.dependency_overrides[deps.get_resolved_principal] = override_get_resolved_principal
    app.dependency_overrides[deps.get_stripe_platform_account_service] = lambda: FakePlatformService

    client = TestClient(app)
    r = client.post(
        "/api/v1/transfers/schedules",
        headers={"Authorization": "Bearer x"},
        json={"interval": "weekly"},
    )
    app.dependency_overrides.clear()

    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Exception handlers (on main app)
# ---------------------------------------------------------------------------


def test_http_exception_handler() -> None:
    from fastapi import HTTPException

    from payme.api.main import app as main_app

    handler = main_app.exception_handlers.get(HTTPException)
    assert handler is not None
    response = handler(None, HTTPException(status_code=400, detail="bad"))
    assert response.status_code == 400
    assert b"bad" in response.body


def test_unhandled_exception_handler() -> None:
    from payme.api.main import app as main_app

    handler = main_app.exception_handlers.get(Exception)
    assert handler is not None
    response = handler(None, RuntimeError("boom"))
    assert response.status_code == 500
    assert b"Internal server error" in response.body
