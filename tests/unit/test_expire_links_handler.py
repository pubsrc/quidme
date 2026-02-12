import payme.handlers.expire_links as expire_links_module


class FakeStripeService:
    """Fake for StripeService(acct_id); single shared instance for handler tests."""

    def __init__(self):
        self.disabled = []

    def disable_payment_link(self, payment_link_id: str) -> None:
        self.disabled.append(payment_link_id)


class FakeStripePlatformService:
    def __init__(self):
        self.disabled = []

    def disable_payment_link(self, payment_link_id: str) -> None:
        self.disabled.append(payment_link_id)


class FakeUserAccountsRepo:
    def __init__(self, stripe_account_id: str = "acct_fake"):
        self.stripe_account_id = stripe_account_id

    def get_primary_for_user(self, user_id: str):
        from types import SimpleNamespace
        return SimpleNamespace(stripe_account_id=self.stripe_account_id)


class FakeLinksRepo:
    def __init__(self, items):
        self._items = items
        self.expired = []

    def list_expired_candidates(self, now_ts):
        return list(self._items)

    def mark_expired(self, link_id):
        self.expired.append(link_id)


class FakeSubsRepo:
    def __init__(self, items):
        self._items = items
        self.expired = []

    def list_expired_candidates(self, now_ts):
        return list(self._items)

    def mark_expired(self, subscription_id):
        self.expired.append(subscription_id)


def test_expire_links_handler(monkeypatch):
    account_stripe_svc = FakeStripeService()
    platform_fake = FakeStripePlatformService()
    accounts_repo = FakeUserAccountsRepo(stripe_account_id="acct_test")
    links_repo = FakeLinksRepo([
        {"link_id": "link-1", "user_id": "user-1", "stripe_payment_link_id": "plink_1", "on_platform": False},
        {"link_id": "link-2", "user_id": "user-2", "stripe_payment_link_id": "plink_platform", "on_platform": True},
    ])
    subs_repo = FakeSubsRepo([
        {"subscription_id": "sub-1", "user_id": "user-1", "stripe_payment_link_id": "plink_2", "on_platform": False},
    ])

    def fake_disable_platform(link_id: str) -> None:
        platform_fake.disable_payment_link(link_id)

    class FakeStripePlatformAccountServiceClass:
        disable_platform_payment_link = staticmethod(fake_disable_platform)

    class FakeStripeConnectedAccountLinkServiceClass:
        @classmethod
        def from_account_id(cls, stripe_account_id: str):
            return account_stripe_svc

    monkeypatch.setattr(expire_links_module, "StripePlatformAccountService", FakeStripePlatformAccountServiceClass)
    monkeypatch.setattr(expire_links_module, "StripeConnectedAccountLinkService", FakeStripeConnectedAccountLinkServiceClass)
    monkeypatch.setattr(expire_links_module, "StripeAccountRepository", lambda: accounts_repo)
    monkeypatch.setattr(expire_links_module, "PaymentLinksRepository", lambda: links_repo)
    monkeypatch.setattr(expire_links_module, "SubscriptionsRepository", lambda: subs_repo)

    result = expire_links_module.handler({}, None)

    assert result == {"expired_links": 2, "expired_subscriptions": 1}
    assert links_repo.expired == ["link-1", "link-2"]
    assert subs_repo.expired == ["sub-1"]
    assert account_stripe_svc.disabled == ["plink_1", "plink_2"]
    assert platform_fake.disabled == ["plink_platform"]
