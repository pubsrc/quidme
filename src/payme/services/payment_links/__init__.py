"""
Payment link creation: base, platform/connected implementations, and factory.

- StripePaymentLinkService: abstract base (one-time and subscription links).
- StripePlatformAccountLinkService: links on the platform account.
- StripeConnectedAccountLinkService: links on a connected account (with application fee).
- StripePaymentLinkFactory: returns platform or connected service based on principal (VERIFIED -> connected).
"""

from __future__ import annotations

from payme.services.payment_links.base import StripePaymentLinkService
from payme.services.payment_links.connected_link_service import StripeConnectedAccountLinkService
from payme.services.payment_links.factory import StripePaymentLinkFactory
from payme.services.payment_links.platform_link_service import StripePlatformAccountLinkService

__all__ = [
    "StripePaymentLinkService",
    "StripePlatformAccountLinkService",
    "StripeConnectedAccountLinkService",
    "StripePaymentLinkFactory",
]
