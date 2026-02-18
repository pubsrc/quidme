"""
Stripe event handling: payment-link and subscription-link payment events.

- payment_intent.succeeded / charge.succeeded: update payment link earnings and store transaction.
- invoice.paid: update subscription link earnings and store transaction (subscription metadata: user_id, link_id).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import stripe

from payme.core.settings import settings
from payme.db.repositories import (
    PaymentLinksRepository,
    StripeAccountRepository,
    SubscriptionsRepository,
    TransactionsRepository,
)

logger = logging.getLogger(__name__)


def _date_transaction_id(created_unix: int | None, payment_intent_id: str) -> str:
    """Sort key: YYYY-MM-DD#payment_intent_id."""
    if created_unix:
        dt = datetime.fromtimestamp(created_unix, tz=timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{date_str}#{payment_intent_id}"


def _to_dict(obj: Any) -> dict[str, Any]:
    """Normalize StripeObject or dict to dict for .get() access."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "get"):
        return dict(obj) if hasattr(obj, "keys") else obj
    return {}


def _earnings_from_base_amount(extracted: dict[str, Any]) -> float:
    """Use base_amount metadata as the single source of truth for earnings."""
    return float(extracted["base_amount"])


def _extract_from_payment_intent(obj: dict[str, Any] | Any) -> dict[str, Any] | None:
    """
    Extract user_id, link_id, amount, payment_intent_id, created, customer fields.
    Returns None if metadata missing user_id or link_id.
    """
    obj = _to_dict(obj)
    metadata = _to_dict(obj.get("metadata") or {})
    user_id = metadata.get("user_id")
    link_id = metadata.get("link_id")
    if not user_id or not link_id:
        return None
    base_amount = metadata.get("base_amount")
    amount = obj.get("amount_received") or obj.get("amount") or 0
    if amount <= 0:
        return None
    payment_intent_id = obj.get("id") or ""
    created = obj.get("created")

    customer_email = None
    customer_name = None
    customer_phone = None
    customer_address = None
    charges = obj.get("charges", {})
    if isinstance(charges, dict) and charges.get("data"):
        first_charge = charges["data"][0]
        if isinstance(first_charge, dict):
            bd = first_charge.get("billing_details") or {}
            customer_email = bd.get("email") or first_charge.get("receipt_email")
            if bd.get("name"):
                customer_name = bd["name"]
            if bd.get("phone"):
                customer_phone = bd["phone"]
            addr = bd.get("address")
            if addr and isinstance(addr, dict):
                parts = [
                    addr.get("line1"),
                    addr.get("line2"),
                    addr.get("city"),
                    addr.get("postal_code"),
                    addr.get("country"),
                ]
                customer_address = ", ".join(p for p in parts if p)

    return {
        "user_id": user_id,
        "link_id": link_id,
        "base_amount": base_amount,
        "amount": amount,
        "currency": (obj.get("currency") or "usd").lower(),
        "payment_intent_id": payment_intent_id,
        "created": created,
        "customer_email": customer_email,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "customer_address": customer_address,
    }


def _extract_from_charge(obj: dict[str, Any] | Any) -> dict[str, Any] | None:
    """Extract from charge.succeeded; requires user_id/link_id in charge metadata."""
    obj = _to_dict(obj)
    metadata = _to_dict(obj.get("metadata") or {})
    user_id = metadata.get("user_id")
    link_id = metadata.get("link_id")
    if not user_id or not link_id:
        return None
    base_amount = metadata.get("base_amount")
    amount = obj.get("amount") or 0
    if amount <= 0:
        return None
    payment_intent_id = obj.get("payment_intent") or obj.get("id") or ""
    if isinstance(payment_intent_id, dict):
        payment_intent_id = payment_intent_id.get("id") or ""
    created = obj.get("created")

    bd = obj.get("billing_details") or {}
    customer_email = bd.get("email") or obj.get("receipt_email")
    customer_name = bd.get("name")
    customer_phone = bd.get("phone")
    customer_address = None
    addr = bd.get("address")
    if addr and isinstance(addr, dict):
        parts = [
            addr.get("line1"),
            addr.get("line2"),
            addr.get("city"),
            addr.get("postal_code"),
            addr.get("country"),
        ]
        customer_address = ", ".join(p for p in parts if p)

    return {
        "user_id": user_id,
        "link_id": link_id,
        "base_amount": base_amount,
        "amount": amount,
        "currency": (obj.get("currency") or "usd").lower(),
        "payment_intent_id": payment_intent_id,
        "created": created,
        "customer_email": customer_email,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "customer_address": customer_address,
    }


def _billing_details_to_customer_dict(
    charge_or_bd: dict[str, Any], *, use_receipt_email: bool = True
) -> dict[str, str | None]:
    """Extract customer_email, customer_name, customer_phone, customer_address from a Charge or billing_details dict."""
    out: dict[str, str | None] = {
        "customer_email": None,
        "customer_name": None,
        "customer_phone": None,
        "customer_address": None,
    }
    bd = charge_or_bd.get("billing_details") if charge_or_bd.get("billing_details") is not None else charge_or_bd
    if not isinstance(bd, dict):
        return out
    out["customer_email"] = (bd.get("email") or (charge_or_bd.get("receipt_email") if use_receipt_email else None)) or None
    out["customer_name"] = bd.get("name") or None
    out["customer_phone"] = bd.get("phone") or None
    addr = bd.get("address")
    if addr and isinstance(addr, dict):
        parts = [
            addr.get("line1"),
            addr.get("line2"),
            addr.get("city"),
            addr.get("postal_code"),
            addr.get("country"),
        ]
        out["customer_address"] = ", ".join(p for p in parts if p) or None
    return out


def _format_address(addr: dict[str, Any] | None) -> str | None:
    """Format Stripe address object to a single line."""
    if not addr or not isinstance(addr, dict):
        return None
    parts = [
        addr.get("line1"),
        addr.get("line2"),
        addr.get("city"),
        addr.get("postal_code"),
        addr.get("state"),
        addr.get("country"),
    ]
    return ", ".join(p for p in parts if p) or None


def _session_customer_details_to_dict(session: dict[str, Any]) -> dict[str, str | None]:
    """Extract customer_email, customer_name, customer_phone, customer_address from a Checkout Session."""
    out: dict[str, str | None] = {
        "customer_email": None,
        "customer_name": None,
        "customer_phone": None,
        "customer_address": None,
    }
    details = session.get("customer_details")
    if isinstance(details, dict):
        out["customer_email"] = details.get("email") or None
        out["customer_name"] = details.get("name") or None
        out["customer_phone"] = details.get("phone") or None
        out["customer_address"] = _format_address(details.get("address"))
    if out["customer_email"] is None:
        out["customer_email"] = session.get("customer_email") or None
    if out["customer_address"] is None:
        out["customer_address"] = _format_address(session.get("customer_address"))
    if out["customer_address"] is None and isinstance(details, dict):
        out["customer_address"] = _format_address(details.get("address"))
    if out["customer_address"] is None:
        shipping = session.get("shipping_details") or session.get("shipping_address")
        if isinstance(shipping, dict) and shipping.get("address"):
            out["customer_address"] = _format_address(shipping.get("address"))
    return out


def _fetch_checkout_session_customer_details(
    payment_intent_id: str, account_id: str | None
) -> dict[str, str | None]:
    """
    For Payment Link / Checkout flows, customer data is stored on the Checkout Session
    (customer_details, address). List sessions by payment_intent and return that data.
    """
    out: dict[str, str | None] = {
        "customer_email": None,
        "customer_name": None,
        "customer_phone": None,
        "customer_address": None,
    }
    stripe.api_key = settings.stripe_secret
    try:
        if account_id:
            sessions = stripe.checkout.Session.list(
                payment_intent=payment_intent_id,
                limit=1,
                stripe_account=account_id,
            )
        else:
            sessions = stripe.checkout.Session.list(
                payment_intent=payment_intent_id,
                limit=1,
            )
    except stripe.StripeError as e:
        logger.debug("Could not list Checkout Sessions for pi=%s: %s", payment_intent_id, e)
        return out
    data = getattr(sessions, "data", None) or (sessions.get("data") if isinstance(sessions, dict) else [])
    if not data or not isinstance(data, list):
        return out
    session = data[0]
    session = _to_dict(session) if not isinstance(session, dict) else session
    return _session_customer_details_to_dict(session)


def _fetch_payment_intent_customer_details(
    payment_intent_id: str, account_id: str | None
) -> dict[str, str | None]:
    """
    Get payee details (email, name, phone, address). For Payment Links, Checkout stores
    them on the Session; we try that first, then fall back to Charge/PaymentMethod.
    Returns dict with keys customer_email, customer_name, customer_phone, customer_address.
    """
    out: dict[str, str | None] = {
        "customer_email": None,
        "customer_name": None,
        "customer_phone": None,
        "customer_address": None,
    }
    # Payment Link uses Checkout: customer data is on the Session (customer_details)
    session_out = _fetch_checkout_session_customer_details(payment_intent_id, account_id)
    if any(session_out.values()):
        return session_out

    stripe.api_key = settings.stripe_secret
    try:
        expand = ["latest_charge", "latest_charge.payment_method"]
        if account_id:
            pi = stripe.PaymentIntent.retrieve(
                payment_intent_id,
                expand=expand,
                stripe_account=account_id,
            )
        else:
            pi = stripe.PaymentIntent.retrieve(
                payment_intent_id,
                expand=expand,
            )
    except stripe.StripeError as e:
        logger.warning("Could not retrieve PaymentIntent for payee details pi=%s: %s", payment_intent_id, e)
        return out
    pi = _to_dict(pi)
    latest = pi.get("latest_charge")
    if isinstance(latest, dict):
        out = _billing_details_to_customer_dict(latest, use_receipt_email=True)
        if out.get("customer_phone") is None:
            pm = latest.get("payment_method")
            if isinstance(pm, dict):
                pm_bd = (pm.get("billing_details") or {}) if isinstance(pm.get("billing_details"), dict) else {}
                if pm_bd.get("phone"):
                    out["customer_phone"] = pm_bd.get("phone")
        if any(out.values()):
            return out
    charges = pi.get("charges", {})
    if isinstance(charges, dict) and charges.get("data"):
        first = charges["data"][0]
        if isinstance(first, dict):
            out = _billing_details_to_customer_dict(first, use_receipt_email=True)
    return out


def handle_payment_succeeded(
    event_type: str, data: dict[str, Any], account_id: str | None = None
) -> bool:
    """
    Handle payment_intent.succeeded or charge.succeeded for payment-link payments.

    Extracts metadata (user_id, link_id, amount, customer info), uses base_amount metadata as
    earnings, adds earnings to the payment link, and stores the transaction in the transactions
    table. If account_id is None (platform-held payment), also adds to user's pending_earnings
    for later transfer when the account is verified.

    Returns True if handled and persisted, False if skipped or error.
    """
    obj = data.get("object")
    if not obj:
        return False

    if event_type == "payment_intent.succeeded":
        extracted = _extract_from_payment_intent(obj)
    elif event_type == "charge.succeeded":
        extracted = _extract_from_charge(obj)
    else:
        return False

    if not extracted:
        logger.info(
            "Payment event %s: missing user_id/link_id in metadata, skipping (set payment_intent_data.metadata on the Payment Link)",
            event_type,
        )
        return False

    user_id = extracted["user_id"]
    link_id = extracted["link_id"]
    amount = extracted["amount"]
    payment_intent_id = extracted["payment_intent_id"] or _to_dict(obj).get("id", "unknown")
    if not payment_intent_id.startswith("pi_"):
        payment_intent_id = f"pi_{payment_intent_id}"

    # Idempotent: already recorded (e.g. from list backfill or duplicate webhook)
    if TransactionsRepository().get_by_payment_intent_id(user_id, payment_intent_id):
        logger.debug("Payment event: transaction already exists pi=%s, skipping", payment_intent_id)
        return True

    # Webhook payload often omits charges.billing_details; fetch so we store email, name, phone, address
    if (
        extracted.get("customer_email") is None
        or extracted.get("customer_name") is None
        or extracted.get("customer_phone") is None
        or extracted.get("customer_address") is None
    ):
        details = _fetch_payment_intent_customer_details(payment_intent_id, account_id)
        for key in ("customer_email", "customer_name", "customer_phone", "customer_address"):
            if extracted.get(key) is None and details.get(key):
                extracted[key] = details[key]

    earnings = _earnings_from_base_amount(extracted)

    date_sk = _date_transaction_id(extracted.get("created"), payment_intent_id)
    created_at = None
    if extracted.get("created"):
        created_at = datetime.fromtimestamp(extracted["created"], tz=timezone.utc).isoformat()

    try:
        transactions_repo = TransactionsRepository()
        transactions_repo.put(
            user_id=user_id,
            date_transaction_id=date_sk,
            payment_intent_id=payment_intent_id,
            link_id=link_id,
            amount=amount,
            currency=extracted["currency"],
            status="succeeded",
            customer_email=extracted.get("customer_email"),
            customer_name=extracted.get("customer_name"),
            customer_phone=extracted.get("customer_phone"),
            customer_address=extracted.get("customer_address"),
            created_at=created_at,
            stripe_account_id=account_id,
        )
        links_repo = PaymentLinksRepository()
        links_repo.add_payment_result(link_id, earnings, amount)
        if account_id is None and earnings > 0:
            StripeAccountRepository().add_pending_earnings(
                user_id, earnings, extracted["currency"]
            )
        if earnings > 0:
            StripeAccountRepository().add_earnings(
                user_id, earnings, extracted["currency"]
            )
    except Exception as e:
        logger.exception(
            "Payment event: failed to store transaction or add earnings: %s", e
        )
        return False

    logger.info(
        "Payment event: stored transaction user_id=%s link_id=%s amount=%s earnings=%s platform_held=%s",
        user_id,
        link_id,
        amount,
        earnings,
        account_id is None,
    )
    return True


def record_payment_succeeded_from_intent(
    intent_obj: dict[str, Any] | Any, account_id: str | None = None
) -> bool:
    """
    Record a one-time payment from a Stripe PaymentIntent (e.g. when listing links and
    backfilling from Stripe). Idempotent: no-op if transaction already exists.
    Returns True if recorded or already existed, False if skipped (e.g. missing metadata).
    """
    extracted = _extract_from_payment_intent(intent_obj)
    if not extracted:
        return False
    return handle_payment_succeeded("payment_intent.succeeded", {"object": intent_obj}, account_id=account_id)


def _extract_minimal_for_failed(obj: dict[str, Any] | Any) -> dict[str, Any] | None:
    """Extract user_id, link_id, amount (requested), etc. from a failed payment_intent."""
    obj = _to_dict(obj)
    metadata = _to_dict(obj.get("metadata") or {})
    user_id = metadata.get("user_id")
    link_id = metadata.get("link_id")
    if not user_id or not link_id:
        return None
    amount = obj.get("amount") or 0
    payment_intent_id = obj.get("id") or ""
    created = obj.get("created")
    return {
        "user_id": user_id,
        "link_id": link_id,
        "amount": amount,
        "currency": (obj.get("currency") or "usd").lower(),
        "payment_intent_id": payment_intent_id,
        "created": created,
        "customer_email": None,
        "customer_name": None,
        "customer_phone": None,
        "customer_address": None,
    }


def handle_payment_failed(
    event_type: str, data: dict[str, Any], account_id: str | None = None
) -> bool:
    """
    Handle payment_intent.payment_failed: store transaction with status=failed.
    Does not update payment link earnings.
    """
    obj = data.get("object")
    if not obj:
        return False
    extracted = _extract_minimal_for_failed(obj)
    if not extracted:
        logger.debug("Payment failed event %s: missing user_id/link_id in metadata, skipping", event_type)
        return False

    user_id = extracted["user_id"]
    link_id = extracted["link_id"]
    amount = extracted["amount"]
    payment_intent_id = extracted["payment_intent_id"] or _to_dict(obj).get("id", "unknown")
    if not payment_intent_id.startswith("pi_"):
        payment_intent_id = f"pi_{payment_intent_id}"

    date_sk = _date_transaction_id(extracted.get("created"), payment_intent_id)
    created_at = None
    if extracted.get("created"):
        created_at = datetime.fromtimestamp(extracted["created"], tz=timezone.utc).isoformat()

    try:
        transactions_repo = TransactionsRepository()
        transactions_repo.put(
            user_id=user_id,
            date_transaction_id=date_sk,
            payment_intent_id=payment_intent_id,
            link_id=link_id,
            amount=amount,
            currency=extracted["currency"],
            status="failed",
            customer_email=extracted.get("customer_email"),
            customer_name=extracted.get("customer_name"),
            customer_phone=extracted.get("customer_phone"),
            customer_address=extracted.get("customer_address"),
            created_at=created_at,
            stripe_account_id=account_id,
        )
    except Exception as e:
        logger.exception("Payment failed event: failed to store transaction: %s", e)
        return False

    logger.info(
        "Payment failed event: stored transaction user_id=%s link_id=%s amount=%s",
        user_id, link_id, amount,
    )
    return True


# -------------------------------------------------------------------------
# Subscription link: invoice.paid
# -------------------------------------------------------------------------


def _metadata_from_invoice_payment_intent(
    invoice_obj: dict[str, Any],
    account_id: str | None,
) -> tuple[str | None, str | None, Any | None]:
    """
    Fallback: get user_id and link_id from the invoice's PaymentIntent metadata.
    Payment Links may not copy subscription_data.metadata onto the Subscription; the
    PaymentIntent for the invoice payment sometimes has the same metadata.
    Returns (user_id, link_id, base_amount) or (None, None, None).
    """
    pi_ref = invoice_obj.get("payment_intent")
    if not pi_ref:
        return (None, None, None)
    pi_id = pi_ref.get("id") if isinstance(pi_ref, dict) else pi_ref
    if not pi_id or not isinstance(pi_id, str):
        return (None, None, None)
    stripe.api_key = settings.stripe_secret
    try:
        if account_id:
            pi = stripe.PaymentIntent.retrieve(pi_id, stripe_account=account_id)
        else:
            pi = stripe.PaymentIntent.retrieve(pi_id)
    except stripe.StripeError as e:
        logger.debug("Could not retrieve invoice payment_intent %s: %s", pi_id, e)
        return (None, None, None)
    pi = _to_dict(pi)
    meta = _to_dict(pi.get("metadata") or {})
    base_amount = meta.get("base_amount")
    return (meta.get("user_id"), meta.get("link_id"), base_amount)


def _extract_from_invoice(
    invoice_obj: dict[str, Any] | Any,
    account_id: str | None,
) -> dict[str, Any] | None:
    """
    Extract user_id, link_id (subscription_id), amount_paid, currency, invoice id, created, customer.
    Prefer metadata from the invoice payload (parent.subscription_details.metadata or
    lines.data[0].metadata) when present; otherwise fetch Subscription from Stripe, then fall back
    to the invoice's PaymentIntent metadata.
    Returns None if all sources lack user_id/link_id.
    """
    obj = _to_dict(invoice_obj)

    # Subscription id: top-level or under parent.subscription_details (Connect) or first line item (renewals)
    subscription_id_stripe = obj.get("subscription")
    if not subscription_id_stripe:
        parent = _to_dict(obj.get("parent") or {})
        sub_details = _to_dict(parent.get("subscription_details") or {})
        subscription_id_stripe = sub_details.get("subscription")
    if not subscription_id_stripe:
        lines = obj.get("lines") or {}
        line_list = lines.get("data") if isinstance(lines, dict) else []
        if line_list and isinstance(line_list[0], dict):
            sub_ref = line_list[0].get("subscription")
            subscription_id_stripe = sub_ref.get("id") if isinstance(sub_ref, dict) else sub_ref
    if subscription_id_stripe and isinstance(subscription_id_stripe, dict):
        subscription_id_stripe = subscription_id_stripe.get("id")
    if not subscription_id_stripe:
        return None

    # Prefer user_id/link_id from invoice payload (parent.subscription_details.metadata or first line)
    user_id = None
    link_id = None
    base_amount: Any | None = None
    parent = _to_dict(obj.get("parent") or {})
    sub_details = _to_dict(parent.get("subscription_details") or {})
    meta = _to_dict(sub_details.get("metadata") or {})
    if meta.get("user_id") and meta.get("link_id"):
        user_id = meta.get("user_id")
        link_id = meta.get("link_id")
        base_amount = meta.get("base_amount")
    if not user_id or not link_id:
        lines = obj.get("lines") or {}
        line_list = lines.get("data") if isinstance(lines, dict) else []
        if line_list and isinstance(line_list[0], dict):
            line_meta = _to_dict(line_list[0].get("metadata") or {})
            if line_meta.get("user_id") and line_meta.get("link_id"):
                user_id = line_meta.get("user_id")
                link_id = line_meta.get("link_id")
                base_amount = line_meta.get("base_amount")

    # Fall back to Subscription object then PaymentIntent
    if not user_id or not link_id:
        stripe.api_key = settings.stripe_secret
        try:
            if account_id:
                sub = stripe.Subscription.retrieve(
                    subscription_id_stripe,
                    stripe_account=account_id,
                )
            else:
                sub = stripe.Subscription.retrieve(subscription_id_stripe)
        except stripe.StripeError as e:
            logger.warning("Failed to retrieve subscription %s: %s", subscription_id_stripe, e)
            return None
        sub = _to_dict(sub)
        metadata = _to_dict(sub.get("metadata") or {})
        user_id = metadata.get("user_id")
        link_id = metadata.get("link_id")
        base_amount = metadata.get("base_amount")

    if not user_id or not link_id:
        user_id, link_id, base_amount = _metadata_from_invoice_payment_intent(obj, account_id)
        if user_id and link_id:
            logger.info(
                "Subscription %s: using user_id/link_id from invoice payment_intent",
                subscription_id_stripe,
            )
            try:
                stripe.api_key = settings.stripe_secret
                if account_id:
                    stripe.Subscription.modify(
                        subscription_id_stripe,
                        stripe_account=account_id,
                        metadata={"user_id": user_id, "link_id": link_id, "base_amount": str(base_amount) if base_amount is not None else ""},
                    )
                else:
                    stripe.Subscription.modify(
                        subscription_id_stripe,
                        metadata={"user_id": user_id, "link_id": link_id, "base_amount": str(base_amount) if base_amount is not None else ""},
                    )
            except stripe.StripeError as e:
                logger.warning("Could not set metadata on subscription %s: %s", subscription_id_stripe, e)

    if not user_id or not link_id:
        return None

    amount = obj.get("amount_paid") or 0
    if amount <= 0:
        return None
    invoice_id = obj.get("id") or ""
    created = obj.get("created")
    currency = (obj.get("currency") or "usd").lower()
    customer_email = obj.get("customer_email")

    return {
        "user_id": user_id,
        "link_id": link_id,
        "base_amount": base_amount,
        "amount": amount,
        "currency": currency,
        "invoice_id": invoice_id,
        "created": created,
        "customer_email": customer_email,
        "customer_name": None,
        "customer_phone": None,
        "customer_address": None,
    }


def handle_invoice_paid(data: dict[str, Any], account_id: str | None = None) -> bool:
    """
    Handle invoice.paid for subscription payment links: store transaction and add earnings to subscription link.
    If account_id is None (platform), add to user's pending_earnings for later transfer.
    Returns True if handled and persisted, False if skipped or error.
    """
    obj = data.get("object")
    if not obj:
        return False
    invoice_id_raw = _to_dict(obj).get("id", "")
    extracted = _extract_from_invoice(obj, account_id)
    if not extracted:
        logger.info(
            "Invoice paid: skipping invoice_id=%s (missing subscription or user_id/link_id). "
            "Ensure checkout.session.completed and subscription metadata are set.",
            invoice_id_raw,
        )
        return False

    user_id = extracted["user_id"]
    link_id = extracted["link_id"]
    amount = extracted["amount"]
    invoice_id = extracted["invoice_id"] or _to_dict(obj).get("id", "unknown")
    if not invoice_id.startswith("in_"):
        invoice_id = f"in_{invoice_id}"
    pi_ref = obj.get("payment_intent") if isinstance(obj, dict) else None
    payment_intent_id = (pi_ref.get("id") if isinstance(pi_ref, dict) else pi_ref) if pi_ref else None
    if not payment_intent_id or not isinstance(payment_intent_id, str) or not payment_intent_id.startswith("pi_"):
        payment_intent_id = invoice_id

    # Idempotent: already recorded (e.g. webhook retry)
    if TransactionsRepository().get_by_payment_intent_id(user_id, payment_intent_id):
        logger.debug("Invoice paid: transaction already exists id=%s, skipping", payment_intent_id)
        return True

    earnings = _earnings_from_base_amount(extracted)

    # Use payment_intent_id for sort key so subscription and one-time transactions interleave
    # (invoice_id would give "in_xxx" which sorts before "pi_xxx", hiding subscriptions in list)
    date_sk = _date_transaction_id(extracted.get("created"), payment_intent_id)
    created_at = None
    if extracted.get("created"):
        created_at = datetime.fromtimestamp(extracted["created"], tz=timezone.utc).isoformat()

    try:
        transactions_repo = TransactionsRepository()
        transactions_repo.put(
            user_id=user_id,
            date_transaction_id=date_sk,
            payment_intent_id=payment_intent_id,
            link_id=link_id,
            amount=amount,
            currency=extracted["currency"],
            status="succeeded",
            customer_email=extracted.get("customer_email"),
            customer_name=extracted.get("customer_name"),
            customer_phone=extracted.get("customer_phone"),
            customer_address=extracted.get("customer_address"),
            created_at=created_at,
            stripe_account_id=account_id,
        )
        subs_repo = SubscriptionsRepository()
        subs_repo.add_payment_result(link_id, earnings, amount)
        if account_id is None and earnings > 0:
            StripeAccountRepository().add_pending_earnings(
                user_id, earnings, extracted["currency"]
            )
        if earnings > 0:
            StripeAccountRepository().add_earnings(
                user_id, earnings, extracted["currency"]
            )
    except Exception as e:
        logger.exception(
            "Invoice paid: failed to store transaction or add earnings: %s", e
        )
        return False

    logger.info(
        "Invoice paid: stored transaction invoice_id=%s user_id=%s link_id=%s amount=%s earnings=%s",
        invoice_id,
        user_id,
        link_id,
        amount,
        earnings,
    )
    return True


def handle_subscription_created(
    data: dict[str, Any], account_id: str | None = None
) -> bool:
    """
    When a Subscription is created (e.g. from a Payment Link), set user_id/link_id on its
    metadata if missing. Payment Links may not copy subscription_data.metadata to the
    Subscription; we try to copy from the first invoice's PaymentIntent so that
    invoice.paid can attribute earnings. Uses latest_invoice -> payment_intent -> metadata.
    """
    obj = data.get("object")
    if not obj:
        return False
    sub = _to_dict(obj)
    sub_id = sub.get("id")
    if not sub_id:
        return False
    metadata = _to_dict(sub.get("metadata") or {})
    if metadata.get("user_id") and metadata.get("link_id"):
        return True

    latest_invoice_ref = sub.get("latest_invoice")
    if not latest_invoice_ref:
        return True
    inv_id = latest_invoice_ref.get("id") if isinstance(latest_invoice_ref, dict) else latest_invoice_ref
    if not inv_id:
        return True

    stripe.api_key = settings.stripe_secret
    try:
        if account_id:
            inv = stripe.Invoice.retrieve(
                inv_id, expand=["payment_intent"], stripe_account=account_id
            )
        else:
            inv = stripe.Invoice.retrieve(inv_id, expand=["payment_intent"])
    except stripe.StripeError as e:
        logger.debug("Subscription %s: could not retrieve invoice %s: %s", sub_id, inv_id, e)
        return True
    inv = _to_dict(inv)
    pi_ref = inv.get("payment_intent")
    if not pi_ref:
        return True
    pi_id = pi_ref.get("id") if isinstance(pi_ref, dict) else pi_ref
    if not pi_id:
        return True
    try:
        if account_id:
            pi = stripe.PaymentIntent.retrieve(pi_id, stripe_account=account_id)
        else:
            pi = stripe.PaymentIntent.retrieve(pi_id)
    except stripe.StripeError as e:
        logger.debug("Subscription %s: could not retrieve payment_intent %s: %s", sub_id, pi_id, e)
        return True
    pi = _to_dict(pi)
    meta = _to_dict(pi.get("metadata") or {})
    user_id = meta.get("user_id")
    link_id = meta.get("link_id")
    base_amount = meta.get("base_amount")
    if not user_id or not link_id:
        return True
    try:
        if account_id:
            stripe.Subscription.modify(
                sub_id,
                stripe_account=account_id,
                metadata={"user_id": user_id, "link_id": link_id, "base_amount": str(base_amount) if base_amount is not None else ""},
            )
        else:
            stripe.Subscription.modify(
                sub_id,
                metadata={"user_id": user_id, "link_id": link_id, "base_amount": str(base_amount) if base_amount is not None else ""},
            )
        logger.info(
            "Subscription %s: set metadata from payment_intent (user_id=%s link_id=%s)",
            sub_id,
            user_id,
            link_id,
        )
    except stripe.StripeError as e:
        logger.warning("Could not set metadata on subscription %s: %s", sub_id, e)
    return True


def handle_checkout_session_completed(
    data: dict[str, Any], account_id: str | None = None
) -> bool:
    """
    When a Checkout Session completes for a subscription (from our Payment Link), set
    user_id/link_id on the Stripe Subscription so invoice.paid can attribute earnings.
    Session has payment_link (Stripe payment link id) and subscription (Stripe subscription id).
    We look up our subscription link by stripe_payment_link_id and then update the Subscription metadata.
    """
    obj = data.get("object")
    if not obj:
        return False
    session = _to_dict(obj)
    if session.get("mode") != "subscription":
        return True
    stripe_subscription_id = session.get("subscription")
    if not stripe_subscription_id:
        return True
    if isinstance(stripe_subscription_id, dict):
        stripe_subscription_id = stripe_subscription_id.get("id")
    if not stripe_subscription_id:
        return True

    payment_link_id = session.get("payment_link")
    if not payment_link_id:
        logger.debug(
            "Checkout session completed for subscription %s but no payment_link on session",
            stripe_subscription_id,
        )
        return True
    if isinstance(payment_link_id, dict):
        payment_link_id = payment_link_id.get("id")
    if not payment_link_id:
        return True

    link = SubscriptionsRepository().get_by_stripe_payment_link_id(payment_link_id)
    if not link:
        logger.debug(
            "Checkout session completed: no subscription link found for payment_link %s",
            payment_link_id,
        )
        return True

    user_id = link.get("user_id")
    link_id = link.get("subscription_id")
    base_amount = link.get("amount")
    if not user_id or not link_id:
        return True

    stripe.api_key = settings.stripe_secret
    try:
        if account_id:
            stripe.Subscription.modify(
                stripe_subscription_id,
                stripe_account=account_id,
                metadata={"user_id": user_id, "link_id": link_id, "base_amount": str(base_amount) if base_amount is not None else ""},
            )
        else:
            stripe.Subscription.modify(
                stripe_subscription_id,
                metadata={"user_id": user_id, "link_id": link_id, "base_amount": str(base_amount) if base_amount is not None else ""},
            )
        logger.info(
            "Checkout session completed: set subscription %s metadata (user_id=%s link_id=%s)",
            stripe_subscription_id,
            user_id,
            link_id,
        )
    except stripe.StripeError as e:
        logger.warning(
            "Could not set metadata on subscription %s: %s",
            stripe_subscription_id,
            e,
        )
        return False
    return True
