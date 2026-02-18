from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from boto3.dynamodb.conditions import Attr, Key

from payme.core.constants import StripeAccountStatus
from payme.core.settings import settings
from payme.db.dynamodb import get_dynamodb_resource


@dataclass
class UserRecord:
    user_id: str
    email: str | None
    stripe_account_id: str | None


class UsersRepository:
    def __init__(self) -> None:
        self._table = get_dynamodb_resource().Table(settings.ddb_table_users)

    def get(self, user_id: str) -> UserRecord | None:
        resp = self._table.get_item(Key={"user_id": user_id})
        item = resp.get("Item")
        if not item:
            return None
        return UserRecord(
            user_id=item["user_id"],
            email=item.get("email"),
            stripe_account_id=item.get("stripe_account_id"),
        )

    def create(self, email: str | None) -> UserRecord:
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "user_id": user_id,
            "email": email,
            "created_at": now,
        }
        self._table.put_item(Item=item, ConditionExpression=Attr("user_id").not_exists())
        return UserRecord(user_id=user_id, email=email, stripe_account_id=None)

    def update_stripe_account(self, user_id: str, stripe_account_id: str) -> None:
        self._table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET stripe_account_id = :sid",
            ExpressionAttributeValues={":sid": stripe_account_id},
        )

    def delete(self, user_id: str) -> None:
        """Delete user record. Only call for the authenticated user (account deletion)."""
        self._table.delete_item(Key={"user_id": user_id})


class UserIdentitiesRepository:
    def __init__(self) -> None:
        self._table = get_dynamodb_resource().Table(settings.ddb_table_user_identities)

    def get(self, provider: str, external_sub: str) -> dict | None:
        identity_id = f"{provider}#{external_sub}"
        resp = self._table.get_item(Key={"identity_id": identity_id})
        return resp.get("Item")

    def create(self, user_id: str, provider: str, external_sub: str, email: str | None) -> None:
        identity_id = f"{provider}#{external_sub}"
        now = datetime.now(timezone.utc).isoformat()
        self._table.put_item(
            Item={
                "identity_id": identity_id,
                "user_id": user_id,
                "provider": provider,
                "external_sub": external_sub,
                "email": email,
                "created_at": now,
            },
            ConditionExpression=Attr("identity_id").not_exists(),
        )

    def get_by_user_id(self, user_id: str) -> list[dict]:
        resp = self._table.query(
            IndexName="user_id_index",
            KeyConditionExpression=Key("user_id").eq(user_id),
        )
        return resp.get("Items", [])

@dataclass
class StripeAccountRecord:
    user_id: str
    stripe_account_id: str
    country: str
    created_at: str
    status: str  # NEW | RESTRICTED | VERIFIED


class StripeAccountRepository:
    """
    Stores Stripe Connect account per user. PK=user_id.
    Only when a record exists here is the user authorized to use payment/subscription APIs.
    Status: NEW (on create) -> RESTRICTED (Stripe deferred account created) -> VERIFIED (onboarding complete).
    """

    def __init__(self) -> None:
        self._table = get_dynamodb_resource().Table(settings.ddb_table_stripe_accounts)

    def get_primary_for_user(self, user_id: str) -> StripeAccountRecord | None:
        """Return the Stripe Connect account for this user, if any."""
        resp = self._table.get_item(Key={"user_id": user_id})
        item = resp.get("Item")
        if not item:
            return None
        return self._item_to_record(item)

    def get_by_stripe_account_id(self, stripe_account_id: str) -> StripeAccountRecord | None:
        """Look up user account by Stripe account id (for webhooks)."""
        resp = self._table.query(
            IndexName="stripe_account_id_index",
            KeyConditionExpression=Key("stripe_account_id").eq(stripe_account_id),
            Limit=1,
        )
        items = resp.get("Items", [])
        if not items:
            return None
        return self._item_to_record(items[0])

    def _item_to_record(self, item: dict) -> StripeAccountRecord:
        return StripeAccountRecord(
            user_id=item["user_id"],
            stripe_account_id=item.get("stripe_account_id") or "",
            country=item.get("country", ""),
            created_at=item.get("created_at", ""),
            status=item.get("status",""),
        )

    def create(self, user_id: str, stripe_account_id: str, country: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        item: dict = {
            "user_id": user_id,
            "country": country,
            "created_at": now,
            "status": StripeAccountStatus.NEW,
        }
        if stripe_account_id and stripe_account_id.strip():
            item["stripe_account_id"] = stripe_account_id.strip()
        self._table.put_item(
            Item=item,
            ConditionExpression=Attr("user_id").not_exists(),
        )

    def update_status(self, user_id: str, status: str) -> None:
        """Update account status (e.g. NEW -> RESTRICTED, RESTRICTED -> VERIFIED)."""
        self._table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET #status = :s",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":s": status},
        )

    def update_stripe_account_id(self, user_id: str, stripe_account_id: str) -> None:
        """Set stripe_account_id and status RESTRICTED (e.g. after creating Connect account)."""
        if not stripe_account_id or not stripe_account_id.strip():
            raise ValueError("stripe_account_id is required")
        self._table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET stripe_account_id = :sid, #status = :s",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":sid": stripe_account_id.strip(), ":s": StripeAccountStatus.RESTRICTED},
        )

    def add_pending_earnings(self, user_id: str, amount_cents: int, currency: str) -> None:
        """Add to pending earnings (platform-held payments) for this user. Currency e.g. 'gbp', 'usd'."""
        c = currency.lower()
        # Two-step update: ensure map exists, then update key (avoids path overlap / moto compatibility).
        self._table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET #pe = if_not_exists(#pe, :empty)",
            ExpressionAttributeNames={"#pe": "pending_earnings"},
            ExpressionAttributeValues={":empty": {}},
        )
        self._table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET #pe.#c = if_not_exists(#pe.#c, :zero) + :amt",
            ExpressionAttributeNames={"#pe": "pending_earnings", "#c": c},
            ExpressionAttributeValues={":zero": 0, ":amt": amount_cents},
        )

    def add_earnings(self, user_id: str, amount_cents: int, currency: str) -> None:
        """Add to total earnings (all-time) for this user's Stripe account. Currency e.g. 'gbp', 'usd'."""
        c = currency.lower()
        # Two-step update: ensure map exists, then update key (avoids path overlap / moto compatibility).
        self._table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET #earnings = if_not_exists(#earnings, :empty)",
            ExpressionAttributeNames={"#earnings": "earnings"},
            ExpressionAttributeValues={":empty": {}},
        )
        self._table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET #earnings.#c = if_not_exists(#earnings.#c, :zero) + :amt",
            ExpressionAttributeNames={"#earnings": "earnings", "#c": c},
            ExpressionAttributeValues={":zero": 0, ":amt": amount_cents},
        )

    def get_earnings(self, user_id: str) -> dict[str, int]:
        """Return total earnings per currency from stripe_accounts table, e.g. {'gbp': 1000, 'usd': 500}."""
        resp = self._table.get_item(Key={"user_id": user_id})
        item = resp.get("Item")
        if not item:
            return {}
        earnings = item.get("earnings")
        if not isinstance(earnings, dict):
            return {}
        return {k: int(v) for k, v in earnings.items() if isinstance(v, (int, float, Decimal)) and int(v) > 0}

    def get_pending_earnings(self, user_id: str) -> dict[str, int]:
        """Return pending earnings per currency (platform-held), e.g. {'gbp': 1000, 'usd': 500}."""
        resp = self._table.get_item(Key={"user_id": user_id})
        item = resp.get("Item")
        if not item:
            return {}
        pe = item.get("pending_earnings")
        if not isinstance(pe, dict):
            return {}
        return {k: int(v) for k, v in pe.items() if isinstance(v, (int, float, Decimal)) and int(v) > 0}

    def clear_pending_earnings(self, user_id: str, only_currencies: list[str] | None = None) -> None:
        """Zero out pending earnings after transfer. If only_currencies is set, only those keys are removed."""
        if not only_currencies:
            self._table.update_item(
                Key={"user_id": user_id},
                UpdateExpression="SET pending_earnings = :empty",
                ExpressionAttributeValues={":empty": {}},
            )
            return
        names = {f"#c{i}": c.lower() for i, c in enumerate(only_currencies)}
        remove_expr = "REMOVE " + ", ".join(f"pending_earnings.#c{i}" for i in range(len(only_currencies)))
        self._table.update_item(
            Key={"user_id": user_id},
            UpdateExpression=remove_expr,
            ExpressionAttributeNames=names,
        )

    def get(self, user_id: str) -> dict | None:
        resp = self._table.get_item(Key={"user_id": user_id})
        return resp.get("Item")

    def delete(self, user_id: str) -> None:
        """Delete Stripe account record for this user. Only call for the authenticated user (account deletion)."""
        self._table.delete_item(Key={"user_id": user_id})


class PaymentLinksRepository:
    def __init__(self) -> None:
        self._table = get_dynamodb_resource().Table(settings.ddb_table_payment_links)

    def create_draft(
        self,
        link_id: str,
        user_id: str,
        title: str | None,
        description: str | None,
        amount: int,
        currency: str,
        expires_at: datetime | None,
        link_type: str,
        require_fields: list[str],
    ) -> str:
        """Create payment link record in DynamoDB before creating in Stripe. No stripe id/url yet."""
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "link_id": link_id,
            "user_id": user_id,
            "title": title,
            "description": description,
            "amount": amount,
            "currency": currency,
            "status": "ACTIVE",
            "link_type": link_type,
            "created_at": now,
            "require_fields": require_fields,
        }
        if expires_at:
            item["expires_at"] = int(expires_at.timestamp())
        self._table.put_item(Item=item)
        return link_id

    def update_with_stripe(
        self,
        link_id: str,
        stripe_payment_link_id: str,
        url: str,
        service_fee: int,
        *,
        on_platform: bool = False,
    ) -> None:
        """After creating the payment link in Stripe, update the DynamoDB record."""
        expr = "SET stripe_payment_link_id = :sid, #url = :url, service_fee = :fee"
        values = {":sid": stripe_payment_link_id, ":url": url, ":fee": service_fee}
        if on_platform:
            expr += ", on_platform = :op"
            values[":op"] = True
        self._table.update_item(
            Key={"link_id": link_id},
            UpdateExpression=expr,
            ExpressionAttributeNames={"#url": "url"},
            ExpressionAttributeValues=values,
        )

    def create(
        self,
        link_id: str,
        user_id: str,
        stripe_payment_link_id: str,
        url: str,
        title: str,
        description: str | None,
        amount: int,
        service_fee: int,
        currency: str,
        expires_at: datetime | None,
        link_type: str,
        require_fields: list[str],
    ) -> str:
        """Create full record (for backward compatibility / tests)."""
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "link_id": link_id,
            "user_id": user_id,
            "stripe_payment_link_id": stripe_payment_link_id,
            "url": url,
            "title": title,
            "description": description,
            "amount": amount,
            "service_fee": service_fee,
            "currency": currency,
            "status": "ACTIVE",
            "link_type": link_type,
            "created_at": now,
            "require_fields": require_fields,
        }
        if expires_at:
            item["expires_at"] = int(expires_at.timestamp())
        self._table.put_item(Item=item)
        return link_id

    def get(self, link_id: str) -> dict | None:
        resp = self._table.get_item(Key={"link_id": link_id})
        return resp.get("Item")

    def mark_expired(self, link_id: str) -> None:
        self._table.update_item(
            Key={"link_id": link_id},
            UpdateExpression="SET #status = :s",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":s": "EXPIRED"},
        )

    def mark_disabled(self, link_id: str) -> None:
        self._table.update_item(
            Key={"link_id": link_id},
            UpdateExpression="SET #status = :s",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":s": "DISABLED"},
        )

    def list_expired_candidates(self, now_ts: int, limit: int = 50) -> list[dict]:
        resp = self._table.query(
            IndexName="status_expires_at_index",
            KeyConditionExpression=Key("status").eq("ACTIVE")
            & Key("expires_at").lte(now_ts),
            Limit=limit,
        )
        return resp.get("Items", [])

    def list_by_user(self, user_id: str, limit: int = 50) -> list[dict]:
        resp = self._table.query(
            IndexName="user_id_index",
            KeyConditionExpression=Key("user_id").eq(user_id),
            Limit=limit,
        )
        return resp.get("Items", [])

    def add_payment_result(self, link_id: str, earnings_amount: int, total_amount: int) -> None:
        """Atomically add earnings and total paid to the payment link (after a successful payment)."""
        if earnings_amount < 0 or total_amount < 0:
            raise ValueError("amounts must be non-negative")
        self._table.update_item(
            Key={"link_id": link_id},
            UpdateExpression="SET earnings_amount = if_not_exists(earnings_amount, :z) + :earn, total_amount_paid = if_not_exists(total_amount_paid, :z) + :tot",
            ExpressionAttributeValues={":z": 0, ":earn": earnings_amount, ":tot": total_amount},
        )

    def delete_all_for_user(self, user_id: str) -> None:
        """Delete all payment links belonging to this user. Only for account deletion."""
        limit = 100
        while True:
            items = self.list_by_user(user_id, limit=limit)
            if not items:
                break
            for item in items:
                self._table.delete_item(Key={"link_id": item["link_id"]})


class TransactionsRepository:
    """
    Stores payment transactions (succeeded and failed). PK=user_id, SK=date_transaction_id.
    date_transaction_id format: YYYY-MM-DD#payment_intent_id.
    Stores transaction and user/payee details only; no earnings_amount.
    """

    def __init__(self) -> None:
        self._table = get_dynamodb_resource().Table(settings.ddb_table_transactions)

    def put(
        self,
        user_id: str,
        date_transaction_id: str,
        payment_intent_id: str,
        link_id: str,
        amount: int,
        currency: str,
        status: str,
        customer_email: str | None = None,
        customer_name: str | None = None,
        customer_phone: str | None = None,
        customer_address: str | None = None,
        created_at: str | None = None,
        stripe_account_id: str | None = None,
    ) -> None:
        """Store a transaction (succeeded or failed). created_at defaults to now (ISO).
        Payee (customer) fields are always stored so DynamoDB has consistent attributes."""
        now = created_at or datetime.now(timezone.utc).isoformat()
        item = {
            "user_id": user_id,
            "date_transaction_id": date_transaction_id,
            "payment_intent_id": payment_intent_id,
            "link_id": link_id,
            "amount": amount,
            "currency": currency,
            "status": status,
            "created_at": now,
            "refunded": False,
            "customer_email": customer_email if customer_email is not None else "",
            "customer_name": customer_name if customer_name is not None else "",
            "customer_phone": customer_phone if customer_phone is not None else "",
            "customer_address": customer_address if customer_address is not None else "",
        }
        if stripe_account_id is not None:
            item["stripe_account_id"] = stripe_account_id
        self._table.put_item(Item=item)

    def get_by_payment_intent_id(
        self, user_id: str, payment_intent_id: str
    ) -> dict | None:
        """Find a transaction by user_id and payment_intent_id (query + filter)."""
        resp = self._table.query(
            KeyConditionExpression=Key("user_id").eq(user_id),
            FilterExpression=Attr("payment_intent_id").eq(payment_intent_id),
            Limit=1,
        )
        items = resp.get("Items", [])
        return items[0] if items else None

    def mark_refunded(
        self, user_id: str, date_transaction_id: str, refund_status: str = "refunded"
    ) -> None:
        """Mark a transaction as refunded."""
        self._table.update_item(
            Key={
                "user_id": user_id,
                "date_transaction_id": date_transaction_id,
            },
            UpdateExpression="SET refunded = :t, refund_status = :s",
            ExpressionAttributeValues={":t": True, ":s": refund_status},
        )

    def list_by_user_and_date_range(
        self,
        user_id: str,
        date_start: str,
        date_end: str,
        limit: int = 100,
        scan_index_forward: bool = True,
    ) -> list[dict]:
        """List transactions for a user between date_start and date_end (inclusive). Dates: YYYY-MM-DD.
        scan_index_forward=False returns newest first."""
        range_end = date_end + "\uffff" if len(date_end) <= 10 else date_end
        resp = self._table.query(
            KeyConditionExpression=Key("user_id").eq(user_id) & Key("date_transaction_id").between(date_start, range_end),
            Limit=limit,
            ScanIndexForward=scan_index_forward,
        )
        return resp.get("Items", [])

    def list_recent(self, user_id: str, limit: int = 25) -> list[dict]:
        """List most recent transactions for a user (from transactions table). Uses last 365 days range, newest first."""
        now = datetime.now(timezone.utc)
        date_end = now.strftime("%Y-%m-%d")
        date_start = (now - timedelta(days=365)).strftime("%Y-%m-%d")
        return self.list_by_user_and_date_range(
            user_id=user_id,
            date_start=date_start,
            date_end=date_end,
            limit=limit,
            scan_index_forward=False,
        )

    def delete_all_for_user(self, user_id: str) -> None:
        """Delete all transactions for this user. Only for account deletion. Uses query + batch delete."""
        table_name = self._table.name
        dynamodb = self._table.meta.client
        batch_size = 25
        while True:
            resp = self._table.query(
                KeyConditionExpression=Key("user_id").eq(user_id),
                Limit=batch_size,
                ProjectionExpression="user_id, date_transaction_id",
            )
            items = resp.get("Items", [])
            if not items:
                break
            request_items = {
                table_name: [
                    {
                        "DeleteRequest": {
                            "Key": {
                                "user_id": it["user_id"],
                                "date_transaction_id": it["date_transaction_id"],
                            }
                        }
                    }
                    for it in items
                ]
            }
            dynamodb.batch_write_item(RequestItems=request_items)


class SubscriptionsRepository:
    def __init__(self) -> None:
        self._table = get_dynamodb_resource().Table(settings.ddb_table_subscription_links)

    def create_draft(
        self,
        subscription_id: str,
        user_id: str,
        title: str | None,
        description: str | None,
        amount: int,
        currency: str,
        interval: str,
        expires_at: datetime | None,
        require_fields: list[str],
    ) -> str:
        """Create subscription link record in DynamoDB before creating in Stripe."""
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "subscription_id": subscription_id,
            "user_id": user_id,
            "title": title,
            "description": description,
            "amount": amount,
            "currency": currency,
            "interval": interval,
            "status": "ACTIVE",
            "created_at": now,
            "require_fields": require_fields,
        }
        if expires_at:
            item["expires_at"] = int(expires_at.timestamp())
        self._table.put_item(Item=item)
        return subscription_id

    def update_with_stripe(
        self,
        subscription_id: str,
        stripe_payment_link_id: str,
        url: str,
        service_fee: int,
        *,
        on_platform: bool = False,
    ) -> None:
        """After creating the subscription payment link in Stripe, update the DynamoDB record."""
        expr = "SET stripe_payment_link_id = :sid, #url = :url, service_fee = :fee"
        values = {":sid": stripe_payment_link_id, ":url": url, ":fee": service_fee}
        if on_platform:
            expr += ", on_platform = :op"
            values[":op"] = True
        self._table.update_item(
            Key={"subscription_id": subscription_id},
            UpdateExpression=expr,
            ExpressionAttributeNames={"#url": "url"},
            ExpressionAttributeValues=values,
        )

    def create(
        self,
        subscription_id: str,
        user_id: str,
        stripe_payment_link_id: str,
        url: str,
        title: str,
        description: str | None,
        amount: int,
        service_fee: int,
        currency: str,
        interval: str,
        expires_at: datetime | None,
        require_fields: list[str],
    ) -> str:
        """Create full record (for backward compatibility / tests)."""
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "subscription_id": subscription_id,
            "user_id": user_id,
            "stripe_payment_link_id": stripe_payment_link_id,
            "url": url,
            "title": title,
            "description": description,
            "amount": amount,
            "service_fee": service_fee,
            "currency": currency,
            "interval": interval,
            "status": "ACTIVE",
            "created_at": now,
            "require_fields": require_fields,
        }
        if expires_at:
            item["expires_at"] = int(expires_at.timestamp())
        self._table.put_item(Item=item)
        return subscription_id

    def get(self, subscription_id: str) -> dict | None:
        resp = self._table.get_item(Key={"subscription_id": subscription_id})
        return resp.get("Item")

    def list_expired_candidates(self, now_ts: int, limit: int = 50) -> list[dict]:
        resp = self._table.query(
            IndexName="status_expires_at_index",
            KeyConditionExpression=Key("status").eq("ACTIVE")
            & Key("expires_at").lte(now_ts),
            Limit=limit,
        )
        return resp.get("Items", [])

    def mark_expired(self, subscription_id: str) -> None:
        self._table.update_item(
            Key={"subscription_id": subscription_id},
            UpdateExpression="SET #status = :s",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":s": "EXPIRED"},
        )

    def mark_disabled(self, subscription_id: str) -> None:
        self._table.update_item(
            Key={"subscription_id": subscription_id},
            UpdateExpression="SET #status = :s",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":s": "DISABLED"},
        )

    def list_by_user(self, user_id: str, limit: int = 50) -> list[dict]:
        resp = self._table.query(
            IndexName="user_id_index",
            KeyConditionExpression=Key("user_id").eq(user_id),
            Limit=limit,
        )
        return resp.get("Items", [])

    def get_by_stripe_payment_link_id(
        self, stripe_payment_link_id: str
    ) -> dict | None:
        """Look up a subscription link by its Stripe payment link id (e.g. from checkout.session.completed)."""
        if not stripe_payment_link_id:
            return None
        resp = self._table.scan(
            FilterExpression=Attr("stripe_payment_link_id").eq(stripe_payment_link_id),
            Limit=1,
        )
        items = resp.get("Items", [])
        return items[0] if items else None

    def add_payment_result(
        self, subscription_id: str, earnings_amount: int, total_amount: int
    ) -> None:
        """Atomically add earnings and total paid to the subscription link (after a successful invoice payment)."""
        if earnings_amount < 0 or total_amount < 0:
            raise ValueError("amounts must be non-negative")
        self._table.update_item(
            Key={"subscription_id": subscription_id},
            UpdateExpression="SET earnings_amount = if_not_exists(earnings_amount, :z) + :earn, total_amount_paid = if_not_exists(total_amount_paid, :z) + :tot",
            ExpressionAttributeValues={":z": 0, ":earn": earnings_amount, ":tot": total_amount},
        )

    def delete_all_for_user(self, user_id: str) -> None:
        """Delete all subscription links belonging to this user. Only for account deletion."""
        limit = 100
        while True:
            items = self.list_by_user(user_id, limit=limit)
            if not items:
                break
            for item in items:
                self._table.delete_item(Key={"subscription_id": item["subscription_id"]})
