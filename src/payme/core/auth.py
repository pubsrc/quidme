from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import requests
from fastapi import HTTPException, Request, status
from jose import jwt

from payme.core.settings import settings
from payme.db.repositories import (
    StripeAccountRecord,
    StripeAccountRepository,
    UserIdentitiesRepository,
    UsersRepository,
)
from payme.services.cloudwatch_metrics import increment_users

# 403 when Stripe account missing or not ready; frontend redirects to /start on this payload
STRIPE_ACCOUNT_REQUIRED_ERROR_CODE = "STRIPE_ACCOUNT_REQUIRED"
STRIPE_ACCOUNT_REQUIRED_PAYLOAD = {
    "error": "FORBIDDEN",
    "error_code": STRIPE_ACCOUNT_REQUIRED_ERROR_CODE,
    "message": "User must complete Stripe account setup before accessing this resource",
    "next_action": "COMPLETE_STRIPE_ONBOARDING",
}


@dataclass(frozen=True)
class Principal:
    """
    Authenticated principal: the logged-in user (from JWT) with Stripe Connect account.
    Resolved by resolve_principal; single source of truth for auth.
    """
    user_id: str
    email: str | None
    external_sub: str
    stripe_account: StripeAccountRecord | None

    @property
    def stripe_account_id(self) -> str | None:
        """Stripe Connect account ID if present, else None."""
        if self.stripe_account is None or not (self.stripe_account.stripe_account_id or "").strip():
            return None
        return self.stripe_account.stripe_account_id


class CognitoJwksCache:
    def __init__(self) -> None:
        self._jwks: dict[str, Any] | None = None
        self._expires_at = 0.0

    def get(self) -> dict[str, Any]:
        now = time.time()
        if self._jwks and now < self._expires_at:
            return self._jwks
        url = (
            f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/"
            f"{settings.cognito_user_pool_id}/.well-known/jwks.json"
        )
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        self._jwks = resp.json()
        self._expires_at = now + 3600
        return self._jwks


_jwks_cache = CognitoJwksCache()


def _get_signing_key(token: str) -> dict[str, Any]:
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    jwks = _jwks_cache.get()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def _decode_token(token: str) -> dict[str, Any]:
    key = _get_signing_key(token)
    issuer = (
        f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/"
        f"{settings.cognito_user_pool_id}"
    )
    try:
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.cognito_app_client_id,
            issuer=issuer,
        )
    except Exception as exc:  # pragma: no cover - precise exceptions vary
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def resolve_principal(
    request: Request,
    identities_repo: UserIdentitiesRepository,
    users_repo: UsersRepository,
    stripe_accounts_repo: StripeAccountRepository,
) -> Principal:
    """
    Single source of truth: resolve principal from JWT and DB (user_id, email, stripe_account).
    Does not enforce Stripe account or status; use require_principal(allowed_statuses) in dependencies for that.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    token = auth_header.split(" ", 1)[1]
    claims = _decode_token(token)

    external_sub = claims.get("sub")
    email = claims.get("email")
    if not external_sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    identity = identities_repo.get("cognito", external_sub)
    if identity:
        user = users_repo.get(identity["user_id"])
        if not user:
            raise HTTPException(status_code=500, detail="User identity mapping broken")
        user_id, user_email = user.user_id, user.email
    else:
        user = users_repo.create(email=email)
        identities_repo.create(user.user_id, "cognito", external_sub, email)
        increment_users()
        user_id, user_email = user.user_id, user.email

    account = stripe_accounts_repo.get_primary_for_user(user_id)
    return Principal(
        user_id=user_id,
        email=user_email,
        external_sub=external_sub,
        stripe_account=account,
    )
