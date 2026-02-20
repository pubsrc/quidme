"""Factory that returns platform or connected payment link service based on principal."""

from __future__ import annotations

from payme.core.auth import Principal
from payme.core.constants import StripeAccountStatus

from payme.services.payment_links.base import StripePaymentLinkService
from payme.services.payment_links.connected_link_service import StripeConnectedAccountLinkService
from payme.services.payment_links.platform_link_service import StripePlatformAccountLinkService


class StripePaymentLinkFactory:
    """Returns the appropriate payment link service: VERIFIED -> connected account; otherwise -> platform."""

    @staticmethod
    def get_link_service(principal: Principal) -> StripePaymentLinkService:
        account = principal.stripe_account
        # todo: use platform account untill connected account webhook is implemented
        # if account is not None and (account.status or "").strip() == StripeAccountStatus.VERIFIED:
            # return StripeConnectedAccountLinkService(principal)
        return StripePlatformAccountLinkService(principal)
