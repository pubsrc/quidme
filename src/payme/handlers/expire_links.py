from __future__ import annotations

import logging
import time

from payme.db.repositories import PaymentLinksRepository, StripeAccountRepository, SubscriptionsRepository
from payme.services.payment_links import StripeConnectedAccountLinkService
from payme.services.stripe_platform_account_service import StripePlatformAccountService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event, context):  # noqa: ANN001
    now_ts = int(time.time())
    links_repo = PaymentLinksRepository()
    subs_repo = SubscriptionsRepository()
    accounts_repo = StripeAccountRepository()

    expired_links = links_repo.list_expired_candidates(now_ts)
    for link in expired_links:
        try:
            if link.get("on_platform"):
                StripePlatformAccountService.disable_platform_payment_link(link["stripe_payment_link_id"])
            else:
                account = accounts_repo.get_primary_for_user(link["user_id"])
                if account:
                    StripeConnectedAccountLinkService.from_account_id(account.stripe_account_id).disable_payment_link(
                        link["stripe_payment_link_id"]
                    )
            links_repo.mark_expired(link["link_id"])
            logger.info("Expired payment link %s", link["link_id"])
        except Exception as exc:  # pragma: no cover - infra error handling
            logger.exception("Failed to expire payment link %s: %s", link.get("link_id"), exc)

    expired_subs = subs_repo.list_expired_candidates(now_ts)
    for sub in expired_subs:
        try:
            if sub.get("on_platform"):
                StripePlatformAccountService.disable_platform_payment_link(sub["stripe_payment_link_id"])
            else:
                account = accounts_repo.get_primary_for_user(sub["user_id"])
                if account:
                    StripeConnectedAccountLinkService.from_account_id(account.stripe_account_id).disable_payment_link(
                        sub["stripe_payment_link_id"]
                    )
            subs_repo.mark_expired(sub["subscription_id"])
            logger.info("Expired subscription link %s", sub["subscription_id"])
        except Exception as exc:  # pragma: no cover - infra error handling
            logger.exception("Failed to expire subscription link %s: %s", sub.get("subscription_id"), exc)

    return {
        "expired_links": len(expired_links),
        "expired_subscriptions": len(expired_subs),
    }
