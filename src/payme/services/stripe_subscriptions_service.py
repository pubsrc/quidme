"""Stripe subscription lifecycle and read/cancel service."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import stripe

from payme.core.settings import settings
from payme.db.repositories import StripeSubscriptionsRepository, SubscriptionsRepository
from payme.models.stripe_subscription import (
    CancelSubscriptionResponse,
    StripeCustomerAddress,
    StripeCustomerDetails,
    StripeSubscriptionItem,
    StripeSubscriptionPlan,
    StripeSubscriptionsResponse,
)

logger = logging.getLogger(__name__)


def _to_dict(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "keys"):
        return dict(obj)
    return {}


def _address_dict(raw: dict[str, Any] | None) -> dict[str, Any] | None:
    if not raw:
        return None
    return {
        "line1": raw.get("line1"),
        "line2": raw.get("line2"),
        "city": raw.get("city"),
        "state": raw.get("state"),
        "postal_code": raw.get("postal_code"),
        "country": raw.get("country"),
    }


def _customer_from_session(session: dict[str, Any]) -> tuple[str | None, str | None, str | None, dict[str, Any] | None]:
    details = _to_dict(session.get("customer_details"))
    email = details.get("email") or session.get("customer_email")
    name = details.get("name")
    phone = details.get("phone")
    address = _address_dict(_to_dict(details.get("address")))
    return name, email, phone, address


def _invoice_subscription_id(invoice: dict[str, Any]) -> str | None:
    sub_id = invoice.get("subscription")
    if isinstance(sub_id, dict):
        sub_id = sub_id.get("id")
    if isinstance(sub_id, str) and sub_id:
        return sub_id

    parent = _to_dict(invoice.get("parent"))
    sub_details = _to_dict(parent.get("subscription_details"))
    sub_id = sub_details.get("subscription")
    if isinstance(sub_id, dict):
        sub_id = sub_id.get("id")
    if isinstance(sub_id, str) and sub_id:
        return sub_id

    lines = _to_dict(invoice.get("lines"))
    items = lines.get("data") or []
    first_line = _to_dict(items[0]) if isinstance(items, list) and items else {}
    parent_obj = _to_dict(first_line.get("parent"))
    sub_item_details = _to_dict(parent_obj.get("subscription_item_details"))
    sub_id = sub_item_details.get("subscription")
    if isinstance(sub_id, dict):
        sub_id = sub_id.get("id")
    return str(sub_id) if sub_id else None


def _invoice_metadata(invoice: dict[str, Any]) -> dict[str, Any]:
    parent = _to_dict(invoice.get("parent"))
    sub_details = _to_dict(parent.get("subscription_details"))
    meta = _to_dict(sub_details.get("metadata"))
    if meta:
        return meta

    lines = _to_dict(invoice.get("lines"))
    items = lines.get("data") or []
    first_line = _to_dict(items[0]) if isinstance(items, list) and items else {}
    meta = _to_dict(first_line.get("metadata"))
    if meta:
        return meta
    return _to_dict(invoice.get("metadata"))


class StripeSubscriptionsService:
    @staticmethod
    def upsert_from_checkout_session_completed(data: dict[str, Any], account_id: str | None = None) -> bool:
        session = _to_dict(data.get("object"))
        if session.get("mode") != "subscription":
            return False

        session_metadata = _to_dict(session.get("metadata"))
        subscription_id = session.get("subscription")
        if isinstance(subscription_id, dict):
            subscription_id = subscription_id.get("id")
        payment_link_id = session.get("payment_link")
        if isinstance(payment_link_id, dict):
            payment_link_id = payment_link_id.get("id")
        if not subscription_id or not payment_link_id:
            return False

        link = SubscriptionsRepository().get_by_stripe_payment_link_id(str(payment_link_id))
        if not link and session_metadata.get("link_id"):
            link = SubscriptionsRepository().get(str(session_metadata["link_id"]))

        if not link:
            user_id = str(session_metadata.get("user_id") or "").strip()
            if not user_id:
                logger.debug("No local subscription link and no user_id metadata for payment link %s", payment_link_id)
                return False
            link = {
                "user_id": user_id,
                "title": session_metadata.get("link_title"),
                "amount": None,
                "currency": session_metadata.get("currency"),
                "interval": session_metadata.get("interval"),
            }

        created_at_ts = int(session.get("created") or int(datetime.now(timezone.utc).timestamp()))
        customer_name, customer_email, customer_phone, customer_address = _customer_from_session(session)

        StripeSubscriptionsRepository().upsert(
            subscription_id=str(subscription_id),
            payment_link_id=str(payment_link_id),
            user_id=str(link.get("user_id")),
            status="active",
            created_at_ts=created_at_ts,
            payment_link_title=link.get("title"),
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            customer_address=customer_address,
            plan_amount=link.get("amount"),
            plan_currency=link.get("currency"),
            plan_interval=link.get("interval"),
            stripe_account_id=account_id,
        )
        return True

    @staticmethod
    def upsert_from_subscription_created(data: dict[str, Any], account_id: str | None = None) -> bool:
        sub = _to_dict(data.get("object"))
        subscription_id = sub.get("id")
        if not subscription_id:
            return False

        metadata = _to_dict(sub.get("metadata"))
        link_id = metadata.get("link_id")
        if not link_id:
            return False

        link = SubscriptionsRepository().get(str(link_id))
        if not link:
            return False
        payment_link_id = link.get("stripe_payment_link_id")
        if not payment_link_id:
            return False

        items = _to_dict(sub.get("items")).get("data") or []
        first_item = _to_dict(items[0]) if isinstance(items, list) and items else {}
        price = _to_dict(first_item.get("price"))

        StripeSubscriptionsRepository().upsert(
            subscription_id=str(subscription_id),
            payment_link_id=str(payment_link_id),
            user_id=str(link.get("user_id")),
            status=str(sub.get("status") or "active"),
            created_at_ts=int(sub.get("created") or int(datetime.now(timezone.utc).timestamp())),
            payment_link_title=link.get("title"),
            plan_amount=price.get("unit_amount") if price else link.get("amount"),
            plan_currency=(price.get("currency") if price else None) or link.get("currency"),
            plan_interval=_to_dict(price.get("recurring")).get("interval") if price else link.get("interval"),
            current_period_start=sub.get("current_period_start"),
            current_period_end=sub.get("current_period_end"),
            stripe_account_id=account_id,
        )
        return True

    @staticmethod
    def mark_canceled_from_subscription_event(data: dict[str, Any]) -> bool:
        sub = _to_dict(data.get("object"))
        subscription_id = sub.get("id")
        if not subscription_id:
            return False
        canceled_at = sub.get("canceled_at") or int(datetime.now(timezone.utc).timestamp())
        return StripeSubscriptionsRepository().mark_canceled(
            subscription_id=str(subscription_id),
            canceled_at_ts=int(canceled_at),
        )

    @staticmethod
    def upsert_from_invoice_paid(data: dict[str, Any], account_id: str | None = None) -> bool:
        invoice = _to_dict(data.get("object"))
        if not invoice:
            return False
        if str(invoice.get("billing_reason") or "").lower() != "subscription_create":
            # Prevent duplicates on recurring renewals; only first paid invoice creates subscriber entry.
            return False

        subscription_id = _invoice_subscription_id(invoice)
        if not subscription_id:
            return False

        meta = _invoice_metadata(invoice)
        link_id = str(meta.get("link_id") or "").strip()
        user_id = str(meta.get("user_id") or "").strip()

        link = SubscriptionsRepository().get(link_id) if link_id else None
        if not user_id and link:
            user_id = str(link.get("user_id") or "")
        if not user_id:
            return False

        payment_link_id = (
            str(link.get("stripe_payment_link_id") or "") if link else ""
        )
        if not payment_link_id:
            # keep a stable non-empty key if the link row is missing/incomplete
            payment_link_id = link_id or f"invoice:{invoice.get('id', 'unknown')}"

        created_at_ts = int(invoice.get("created") or int(datetime.now(timezone.utc).timestamp()))
        customer_name = invoice.get("customer_name")
        customer_email = invoice.get("customer_email")
        customer_phone = invoice.get("customer_phone")
        customer_address = _address_dict(_to_dict(invoice.get("customer_address")))

        lines = _to_dict(invoice.get("lines"))
        items = lines.get("data") or []
        first_line = _to_dict(items[0]) if isinstance(items, list) and items else {}
        period = _to_dict(first_line.get("period"))

        StripeSubscriptionsRepository().upsert(
            subscription_id=str(subscription_id),
            payment_link_id=str(payment_link_id),
            user_id=str(user_id),
            status="active" if str(invoice.get("status") or "").lower() == "paid" else str(invoice.get("status") or "active"),
            created_at_ts=created_at_ts,
            payment_link_title=(link.get("title") if link else None) or meta.get("link_title"),
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            customer_address=customer_address,
            plan_amount=link.get("amount") if link else None,
            plan_currency=(link.get("currency") if link else None) or invoice.get("currency"),
            plan_interval=(link.get("interval") if link else None) or meta.get("interval"),
            current_period_start=period.get("start") or invoice.get("period_start"),
            current_period_end=period.get("end") or invoice.get("period_end"),
            stripe_account_id=account_id,
        )
        return True

    @staticmethod
    def list_user_subscriptions(user_id: str, *, limit: int = 25, page: str | None = None) -> StripeSubscriptionsResponse:
        items, has_more, next_cursor = StripeSubscriptionsRepository().list_by_user_paginated(
            user_id, limit=limit, page=page
        )
        result: list[StripeSubscriptionItem] = []
        for item in items:
            result.append(
                StripeSubscriptionItem(
                    id=item["subscription_id"],
                    status=item.get("status", "active"),
                    payment_link_title=item.get("payment_link_title"),
                    created_at=datetime.fromtimestamp(
                        int(item.get("created_at_ts")), tz=timezone.utc
                    )
                    if item.get("created_at_ts") is not None
                    else None,
                    current_period_start=item.get("current_period_start"),
                    current_period_end=item.get("current_period_end"),
                    cancel_at_period_end=item.get("cancel_at_period_end"),
                    customer=StripeCustomerDetails(
                        name=item.get("customer_name"),
                        email=item.get("customer_email"),
                        phone=item.get("customer_phone"),
                        address=StripeCustomerAddress(**item.get("customer_address", {}))
                        if item.get("customer_address")
                        else None,
                    ),
                    plan=StripeSubscriptionPlan(
                        amount=item.get("plan_amount"),
                        currency=item.get("plan_currency"),
                        interval=item.get("plan_interval"),
                    ),
                )
            )
        return StripeSubscriptionsResponse(items=result, has_more=has_more, next_cursor=next_cursor)

    @staticmethod
    def cancel_subscription_for_user(user_id: str, subscription_id: str) -> CancelSubscriptionResponse:
        record = StripeSubscriptionsRepository().get_for_user(user_id, subscription_id)
        if not record:
            raise ValueError("Subscription not found")

        stripe.api_key = settings.stripe_secret
        stripe_account_id = record.get("stripe_account_id")
        if stripe_account_id:
            stripe.Subscription.cancel(subscription_id, stripe_account=stripe_account_id)
        else:
            stripe.Subscription.cancel(subscription_id)

        StripeSubscriptionsRepository().mark_canceled(
            subscription_id=subscription_id,
            canceled_at_ts=int(datetime.now(timezone.utc).timestamp()),
        )
        return CancelSubscriptionResponse(id=subscription_id, status="canceled")
