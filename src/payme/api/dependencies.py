"""FastAPI dependencies for authentication, authorization, repositories, and Stripe services."""

from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Request, status

from payme.core.auth import Principal, STRIPE_ACCOUNT_REQUIRED_PAYLOAD, resolve_principal
from payme.core.constants import StripeAccountStatus
from payme.db.repositories import (
    PaymentLinksRepository,
    StripeSubscriptionsRepository,
    StripeAccountRepository,
    SubscriptionsRepository,
    TransactionsRepository,
    UserIdentitiesRepository,
    UsersRepository,
)
from payme.services.payment_links import (
    StripeConnectedAccountLinkService,
    StripePaymentLinkFactory,
    StripePaymentLinkService,
)
from payme.services.stripe_platform_account_service import StripePlatformAccountService

# Re-export for main app exception handler
from payme.core.auth import STRIPE_ACCOUNT_REQUIRED_ERROR_CODE  # noqa: F401


# -------------------------------------------------------------------------
# Repositories
# -------------------------------------------------------------------------


def get_users_repository() -> UsersRepository:
    return UsersRepository()


def get_user_identities_repository() -> UserIdentitiesRepository:
    return UserIdentitiesRepository()


def get_stripe_accounts_repository() -> StripeAccountRepository:
    return StripeAccountRepository()


# -------------------------------------------------------------------------
# Auth (single source: resolve_principal in core.auth; require_principal enforces status)
# -------------------------------------------------------------------------


def get_resolved_principal(
    request: Request,
    identities_repository: Annotated[UserIdentitiesRepository, Depends(get_user_identities_repository)],
    users_repository: Annotated[UsersRepository, Depends(get_users_repository)],
    stripe_accounts_repository: Annotated[StripeAccountRepository, Depends(get_stripe_accounts_repository)],
) -> Principal:
    """Resolve principal from JWT and DB. No status check; use require_principal(...) for that."""
    return resolve_principal(
        request,
        identities_repository,
        users_repository,
        stripe_accounts_repository,
    )


def require_principal(
    *allowed_statuses: str | None,
) -> Callable[..., Principal]:
    """
    Returns a dependency that resolves principal and optionally enforces Stripe account status.
    - require_principal(None): no check, return principal (e.g. POST /platform/connected-accounts).
    - require_principal(): require account and status in (RESTRICTED, VERIFIED); 403 otherwise.
    - require_principal(StripeAccountStatus.VERIFIED): require VERIFIED only.
    """

    def _dependency(
        principal: Annotated[Principal, Depends(get_resolved_principal)],
    ) -> Principal:
       

        if allowed_statuses is not None and len(allowed_statuses) == 1 and allowed_statuses[0] is None:
            return principal
        statuses = list(allowed_statuses) if allowed_statuses else [
            StripeAccountStatus.NEW,StripeAccountStatus.RESTRICTED, StripeAccountStatus.VERIFIED]
        if not statuses:
            return principal
        
        prinicipal_status = principal.stripe_account.status if principal.stripe_account and principal.stripe_account.status else ""
        current = prinicipal_status.strip().upper()

        if current not in [s.strip().upper() for s in statuses if s]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=STRIPE_ACCOUNT_REQUIRED_PAYLOAD,
            )
        return principal

    return _dependency


def get_payment_links_repository() -> PaymentLinksRepository:
    return PaymentLinksRepository()


def get_subscriptions_repository() -> SubscriptionsRepository:
    return SubscriptionsRepository()


def get_stripe_subscriptions_repository() -> StripeSubscriptionsRepository:
    return StripeSubscriptionsRepository()


def get_transactions_repository() -> TransactionsRepository:
    return TransactionsRepository()


# -------------------------------------------------------------------------
# Stripe services
# -------------------------------------------------------------------------


def get_stripe_platform_account_service() -> type[StripePlatformAccountService]:
    """Platform (admin) service: create connected accounts, onboarding links, disable platform links."""
    return StripePlatformAccountService


def get_stripe_link_service(
    principal: Annotated[Principal, Depends(require_principal())],
) -> StripePaymentLinkService:
    """Payment link service (platform or connected) from factory. VERIFIED -> connected; otherwise -> platform."""
    return StripePaymentLinkFactory.get_link_service(principal)


def get_stripe_connected_account_link_service_optional(
    principal: Annotated[Principal, Depends(require_principal())],
) -> StripeConnectedAccountLinkService | None:
    """Connected account link service when user has stripe_account_id; None otherwise (for list payment links)."""
    if principal.stripe_account is None or not (principal.stripe_account_id or "").strip():
        return None
    if (principal.stripe_account.status or "").strip() != StripeAccountStatus.VERIFIED:
        return None
    return StripeConnectedAccountLinkService(principal)


def get_stripe_platform_account_link_service(
    principal: Annotated[Principal, Depends(require_principal())],
) -> StripePaymentLinkService:
    """Platform account link service instance (for list when on_platform)."""
    from payme.services.payment_links import StripePlatformAccountLinkService
    return StripePlatformAccountLinkService(principal)
