"""Unit tests for StripePaymentLinkFactory: platform vs connected link service by account status."""

from __future__ import annotations

from payme.core.auth import Principal
from payme.core.constants import StripeAccountStatus
from payme.db.repositories import StripeAccountRecord
from payme.services.payment_links import StripePaymentLinkFactory
from payme.services.payment_links.connected_link_service import StripeConnectedAccountLinkService
from payme.services.payment_links.platform_link_service import StripePlatformAccountLinkService


def _principal(
    user_id: str = "user-1",
    stripe_account: StripeAccountRecord | None = None,
) -> Principal:
    return Principal(
        user_id=user_id,
        email="test@example.com",
        external_sub="ext-1",
        stripe_account=stripe_account,
    )


def _account_record(status: str, stripe_account_id: str = "acct_123") -> StripeAccountRecord:
    return StripeAccountRecord(
        user_id="user-1",
        stripe_account_id=stripe_account_id,
        country="GB",
        created_at="2025-01-01T00:00:00Z",
        status=status,
    )


def test_get_link_service_no_account_returns_platform() -> None:
    """When principal has no Stripe account, factory returns platform link service."""
    principal = _principal(stripe_account=None)
    service = StripePaymentLinkFactory.get_link_service(principal)
    assert isinstance(service, StripePlatformAccountLinkService)
    assert service.is_platform is True


def test_get_link_service_status_new_returns_platform() -> None:
    """When account status is NEW, factory returns platform link service."""
    principal = _principal(stripe_account=_account_record(StripeAccountStatus.NEW))
    service = StripePaymentLinkFactory.get_link_service(principal)
    assert isinstance(service, StripePlatformAccountLinkService)
    assert service.is_platform is True


def test_get_link_service_status_restricted_returns_platform() -> None:
    """When account status is RESTRICTED, factory returns platform link service."""
    principal = _principal(stripe_account=_account_record(StripeAccountStatus.RESTRICTED))
    service = StripePaymentLinkFactory.get_link_service(principal)
    assert isinstance(service, StripePlatformAccountLinkService)
    assert service.is_platform is True


def test_get_link_service_status_verified_returns_connected() -> None:
    """When account status is VERIFIED, factory returns connected account link service."""
    principal = _principal(stripe_account=_account_record(StripeAccountStatus.VERIFIED))
    service = StripePaymentLinkFactory.get_link_service(principal)
    assert isinstance(service, StripeConnectedAccountLinkService)
    assert service.is_platform is False
    assert service.stripe_account_id == "acct_123"


def test_get_link_service_status_empty_returns_platform() -> None:
    """When account status is empty string, factory returns platform link service."""
    principal = _principal(stripe_account=_account_record(""))
    service = StripePaymentLinkFactory.get_link_service(principal)
    assert isinstance(service, StripePlatformAccountLinkService)
    assert service.is_platform is True


def test_get_link_service_status_whitespace_returns_platform() -> None:
    """When account status is whitespace-only, factory returns platform link service."""
    principal = _principal(stripe_account=_account_record("  "))
    service = StripePaymentLinkFactory.get_link_service(principal)
    assert isinstance(service, StripePlatformAccountLinkService)
    assert service.is_platform is True


def test_get_link_service_status_verified_lowercase_returns_platform() -> None:
    """Only exact VERIFIED (after strip) returns connected; lowercase 'verified' returns platform."""
    principal = _principal(stripe_account=_account_record("verified"))
    service = StripePaymentLinkFactory.get_link_service(principal)
    assert isinstance(service, StripePlatformAccountLinkService)
    assert service.is_platform is True
