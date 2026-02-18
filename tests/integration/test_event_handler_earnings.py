"""Integration tests for Stripe event handling.

Use real DynamoDB (moto) to assert that handle_payment_succeeded and handle_invoice_paid
update earnings in both payment/subscription links and in the stripe_accounts table.
"""

from __future__ import annotations

from datetime import datetime, timezone

import boto3
from moto import mock_aws

from payme.db.repositories import (
    PaymentLinksRepository,
    StripeAccountRepository,
    SubscriptionsRepository,
    TransactionsRepository,
    UsersRepository,
)
from payme.services.stripe_event_handler import handle_invoice_paid, handle_payment_succeeded


def _create_tables() -> None:
    """Create DynamoDB tables used by event handlers (matches test_repositories + transactions)."""
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")

    dynamodb.create_table(
        TableName="payme-users",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="payme-stripe-accounts",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "stripe_account_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "stripe_account_id_index",
                "KeySchema": [{"AttributeName": "stripe_account_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="payme-payment-links",
        KeySchema=[{"AttributeName": "link_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "link_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "status", "AttributeType": "S"},
            {"AttributeName": "expires_at", "AttributeType": "N"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "user_id_index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "status_expires_at_index",
                "KeySchema": [
                    {"AttributeName": "status", "KeyType": "HASH"},
                    {"AttributeName": "expires_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="payme-transactions",
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "date_transaction_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "date_transaction_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="payme-subscription-links",
        KeySchema=[{"AttributeName": "subscription_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "subscription_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "status", "AttributeType": "S"},
            {"AttributeName": "expires_at", "AttributeType": "N"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "user_id_index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "status_expires_at_index",
                "KeySchema": [
                    {"AttributeName": "status", "KeyType": "HASH"},
                    {"AttributeName": "expires_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )


def _payment_intent_event(user_id: str, link_id: str, amount: int = 1000, currency: str = "gbp") -> dict:
    return {
        "object": {
            "id": "pi_test_123",
            "amount_received": amount,
            "amount": amount,
            "currency": currency,
            "created": int(datetime.now(timezone.utc).timestamp()),
            "metadata": {
                "user_id": user_id,
                "link_id": link_id,
                "base_amount": str(amount),
                "account_type": "platform",
            },
            "charges": {"data": []},
        }
    }


def _invoice_paid_event(
    user_id: str, link_id: str, amount: int = 2000, currency: str = "usd", payment_intent_id: str = "pi_inv_456"
) -> dict:
    return {
        "object": {
            "id": "in_test_789",
            "amount_paid": amount,
            "currency": currency,
            "created": int(datetime.now(timezone.utc).timestamp()),
            "customer_email": "cust@example.com",
            "payment_intent": {"id": payment_intent_id},
            "subscription": "sub_stripe_1",
            "lines": {"data": [{"metadata": {"user_id": user_id, "link_id": link_id, "base_amount": str(amount)}}]},
        }
    }


@mock_aws
def test_handle_payment_succeeded_earnings_in_payment_link_and_stripe_account() -> None:
    """After payment_intent.succeeded, payment link earnings_amount and stripe_accounts earnings are updated in DynamoDB."""
    _create_tables()
    users_repo = UsersRepository()
    accounts_repo = StripeAccountRepository()
    links_repo = PaymentLinksRepository()
    tx_repo = TransactionsRepository()

    user = users_repo.create(email="seller@example.com")
    user_id = user.user_id
    accounts_repo.create(user_id, "acct_123", "GB")

    link_id = "link-earn-1"
    amount = 1000
    service_fee = 55
    expected_earnings = amount
    links_repo.create(
        link_id=link_id,
        user_id=user_id,
        stripe_payment_link_id="plink_1",
        url="https://checkout.example.com/x",
        title="Test",
        description=None,
        amount=amount,
        service_fee=service_fee,
        currency="gbp",
        expires_at=datetime.now(timezone.utc),
        link_type="one_time",
        require_fields=["email", "name"],
    )

    data = _payment_intent_event(user_id=user_id, link_id=link_id, amount=amount, currency="gbp")
    result = handle_payment_succeeded("payment_intent.succeeded", data, account_id=None)

    assert result is True

    link = links_repo.get(link_id)
    assert link is not None
    assert link.get("earnings_amount") == expected_earnings
    assert link.get("total_amount_paid") == amount

    earnings = accounts_repo.get_earnings(user_id)
    assert earnings.get("gbp") == expected_earnings

    items = tx_repo.list_by_user_and_date_range(
        user_id=user_id,
        date_start="2020-01-01",
        date_end="2030-12-31",
        limit=10,
    )
    assert len(items) == 1
    assert items[0]["payment_intent_id"] == "pi_test_123"
    assert items[0]["amount"] == amount


@mock_aws
def test_handle_invoice_paid_earnings_in_subscription_link_and_stripe_account() -> None:
    """After invoice.paid, subscription link earnings_amount and stripe_accounts earnings are updated in DynamoDB."""
    _create_tables()
    users_repo = UsersRepository()
    accounts_repo = StripeAccountRepository()
    subs_repo = SubscriptionsRepository()
    tx_repo = TransactionsRepository()

    user = users_repo.create(email="subseller@example.com")
    user_id = user.user_id
    accounts_repo.create(user_id, "acct_456", "GB")

    link_id = "sub-earn-1"
    amount = 3000
    service_fee = 150
    expected_earnings = amount
    subs_repo.create(
        subscription_id=link_id,
        user_id=user_id,
        stripe_payment_link_id="plink_sub_1",
        url="https://checkout.example.com/s",
        title="Sub",
        description=None,
        amount=amount,
        service_fee=service_fee,
        currency="gbp",
        interval="month",
        expires_at=None,
        require_fields=["email", "name"],
    )

    data = _invoice_paid_event(user_id=user_id, link_id=link_id, amount=amount, currency="gbp")
    result = handle_invoice_paid(data, account_id=None)

    assert result is True

    sub_link = subs_repo.get(link_id)
    assert sub_link is not None
    assert sub_link.get("earnings_amount") == expected_earnings
    assert sub_link.get("total_amount_paid") == amount

    earnings = accounts_repo.get_earnings(user_id)
    assert earnings.get("gbp") == expected_earnings

    items = tx_repo.list_by_user_and_date_range(
        user_id=user_id,
        date_start="2020-01-01",
        date_end="2030-12-31",
        limit=10,
    )
    assert len(items) == 1
    assert items[0]["amount"] == amount
