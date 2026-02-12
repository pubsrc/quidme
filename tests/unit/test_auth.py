import time

import payme.core.auth as auth_module
from payme.core.auth import CognitoJwksCache, Principal, _get_signing_key, resolve_principal
from payme.db.repositories import UserRecord


class FakeStripeAccountRepository:
    def __init__(self, account=None):
        self._account = account

    def get_primary_for_user(self, user_id: str):
        return self._account


class FakeUsersRepository:
    def __init__(self, users):
        self._users = users
        self._created = []

    def get(self, user_id):
        return self._users.get(user_id)

    def create(self, email):
        record = UserRecord(user_id="user-new", email=email, stripe_account_id=None)
        self._users[record.user_id] = record
        self._created.append(record)
        return record


class FakeUserIdentitiesRepository:
    def __init__(self, identities):
        self._identities = identities
        self._created = []

    def get(self, provider, external_sub):
        return self._identities.get((provider, external_sub))

    def create(self, user_id, provider, external_sub, email):
        item = {
            "identity_id": f"{provider}#{external_sub}",
            "user_id": user_id,
            "provider": provider,
            "external_sub": external_sub,
            "email": email,
        }
        self._identities[(provider, external_sub)] = item
        self._created.append(item)


class FakeRequest:
    def __init__(self, token):
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"


def test_resolve_principal_missing_token():
    request = FakeRequest(token=None)
    identities_repo = FakeUserIdentitiesRepository({})
    users_repo = FakeUsersRepository({})
    accounts_repo = FakeStripeAccountRepository(None)
    try:
        resolve_principal(request, identities_repo, users_repo, accounts_repo)
    except Exception as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("Expected HTTPException")


def test_resolve_principal_existing_identity(monkeypatch):
    users = {
        "user-1": UserRecord(user_id="user-1", email="test@example.com", stripe_account_id=None)
    }
    identities = {("cognito", "sub-123"): {"user_id": "user-1"}}

    monkeypatch.setattr(auth_module, "_decode_token", lambda token: {"sub": "sub-123", "email": "test@example.com"})

    identities_repo = FakeUserIdentitiesRepository(identities)
    users_repo = FakeUsersRepository(users)
    accounts_repo = FakeStripeAccountRepository(None)

    principal = resolve_principal(
        FakeRequest(token="token"), identities_repo, users_repo, accounts_repo
    )
    assert isinstance(principal, Principal)
    assert principal.user_id == "user-1"
    assert principal.email == "test@example.com"
    assert principal.stripe_account is None


def test_resolve_principal_creates_identity(monkeypatch):
    users = {}
    identities = {}

    fake_users_repo = FakeUsersRepository(users)
    fake_identities_repo = FakeUserIdentitiesRepository(identities)
    fake_accounts_repo = FakeStripeAccountRepository(None)

    monkeypatch.setattr(auth_module, "_decode_token", lambda token: {"sub": "sub-new", "email": "new@example.com"})

    principal = resolve_principal(
        FakeRequest(token="token"),
        fake_identities_repo,
        fake_users_repo,
        fake_accounts_repo,
    )
    assert principal.user_id == "user-new"
    assert fake_users_repo._created
    assert fake_identities_repo._created


def test_jwks_cache_fetches(monkeypatch):
    class FakeResponse:
        def __init__(self):
            self._json = {"keys": [{"kid": "kid-1"}]}

        def raise_for_status(self):
            return None

        def json(self):
            return self._json

    monkeypatch.setattr(auth_module.requests, "get", lambda url, timeout: FakeResponse())

    cache = CognitoJwksCache()
    jwks = cache.get()

    assert jwks["keys"][0]["kid"] == "kid-1"
    assert cache._expires_at > time.time()


def test_get_signing_key_found(monkeypatch):
    monkeypatch.setattr(auth_module.jwt, "get_unverified_header", lambda token: {"kid": "kid-1"})
    monkeypatch.setattr(auth_module._jwks_cache, "get", lambda: {"keys": [{"kid": "kid-1", "kty": "RSA"}]})

    key = _get_signing_key("token")
    assert key["kid"] == "kid-1"


def test_get_signing_key_missing(monkeypatch):
    monkeypatch.setattr(auth_module.jwt, "get_unverified_header", lambda token: {"kid": "kid-2"})
    monkeypatch.setattr(auth_module._jwks_cache, "get", lambda: {"keys": [{"kid": "kid-1"}]})

    try:
        _get_signing_key("token")
    except Exception as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("Expected HTTPException")
