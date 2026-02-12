from datetime import datetime, timezone

import boto3
from moto import mock_aws

from payme.db.repositories import (
    PaymentLinksRepository,
    SubscriptionsRepository,
    StripeAccountRepository,
    UserIdentitiesRepository,
    UsersRepository,
)


def _create_tables():
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")

    dynamodb.create_table(
        TableName="payme-users",
        KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName="payme-user-identities",
        KeySchema=[{"AttributeName": "identity_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "identity_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "user_id_index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
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
            }
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
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )


@mock_aws
def test_user_identity_mapping_roundtrip():
    _create_tables()
    users_repo = UsersRepository()
    identities_repo = UserIdentitiesRepository()

    user = users_repo.create(email="test@example.com")
    identities_repo.create(user.user_id, "cognito", "sub-123", "test@example.com")

    identity = identities_repo.get("cognito", "sub-123")
    assert identity["user_id"] == user.user_id


@mock_aws
def test_user_accounts_create_and_get():
    _create_tables()
    users_repo = UsersRepository()
    accounts_repo = StripeAccountRepository()

    user = users_repo.create(email="test@example.com")
    accounts_repo.create(user.user_id, "acct_123", "GB")

    account = accounts_repo.get_primary_for_user(user.user_id)
    assert account is not None
    assert account.user_id == user.user_id
    assert account.stripe_account_id == "acct_123"
    assert account.country == "GB"
    assert account.status == "NEW"

    by_stripe = accounts_repo.get_by_stripe_account_id("acct_123")
    assert by_stripe is not None
    assert by_stripe.user_id == user.user_id

    accounts_repo.update_status(user.user_id, "VERIFIED")
    account = accounts_repo.get_primary_for_user(user.user_id)
    assert account.status == "VERIFIED"


@mock_aws
def test_user_accounts_one_per_user():
    """Enforce 1-1: a user can have only one Stripe account; second create for same user_id fails."""
    import botocore.exceptions

    _create_tables()
    users_repo = UsersRepository()
    accounts_repo = StripeAccountRepository()

    user = users_repo.create(email="test@example.com")
    accounts_repo.create(user.user_id, "acct_first", "GB")

    try:
        accounts_repo.create(user.user_id, "acct_second", "GB")
        assert False, "Expected ConditionalCheckFailedException"
    except botocore.exceptions.ClientError as e:
        assert e.response["Error"]["Code"] == "ConditionalCheckFailedException"

    account = accounts_repo.get_primary_for_user(user.user_id)
    assert account.stripe_account_id == "acct_first"


@mock_aws
def test_user_identity_get_by_user_id():
    _create_tables()
    users_repo = UsersRepository()
    identities_repo = UserIdentitiesRepository()

    user = users_repo.create(email="test@example.com")
    identities_repo.create(user.user_id, "cognito", "sub-123", "test@example.com")
    identities_repo.create(user.user_id, "google", "sub-999", "test@example.com")

    results = identities_repo.get_by_user_id(user.user_id)

    assert len(results) == 2
    providers = {item["provider"] for item in results}
    assert providers == {"cognito", "google"}


@mock_aws
def test_payment_link_create_draft_and_update_with_stripe():
    _create_tables()
    links_repo = PaymentLinksRepository()

    link_id = "link-draft-1"
    user_id = "user-1"
    links_repo.create_draft(
        link_id=link_id,
        user_id=user_id,
        title="Draft",
        description=None,
        amount=100,
        currency="gbp",
        expires_at=None,
        link_type="one_time",
        require_fields=["email", "name"],
    )
    item = links_repo.get(link_id)
    assert item is not None
    assert item["user_id"] == user_id
    assert item["amount"] == 100
    assert "stripe_payment_link_id" not in item or item.get("stripe_payment_link_id") is None

    links_repo.update_with_stripe(link_id, "plink_stripe_1", "https://checkout.stripe.com/x", 55)
    item2 = links_repo.get(link_id)
    assert item2["stripe_payment_link_id"] == "plink_stripe_1"
    assert item2["url"] == "https://checkout.stripe.com/x"
    assert item2["service_fee"] == 55


@mock_aws
def test_payment_link_expiry_query():
    _create_tables()
    links_repo = PaymentLinksRepository()

    link_id = "link-1"
    links_repo.create(
        link_id=link_id,
        user_id="user-1",
        stripe_payment_link_id="plink_1",
        url="https://example.com",
        title="Test",
        description=None,
        amount=100,
        service_fee=5,
        currency="usd",
        expires_at=datetime.now(timezone.utc),
        link_type="one_time",
        require_fields=["email", "name"],
    )

    results = links_repo.list_expired_candidates(int(datetime.now(timezone.utc).timestamp()) + 1)
    assert len(results) == 1
    assert results[0]["link_id"] == link_id


@mock_aws
def test_payment_links_list_by_user_and_status_updates():
    _create_tables()
    links_repo = PaymentLinksRepository()

    links_repo.create(
        link_id="link-1",
        user_id="user-1",
        stripe_payment_link_id="plink_1",
        url="https://example.com",
        title="Test",
        description=None,
        amount=100,
        service_fee=5,
        currency="usd",
        expires_at=None,
        link_type="one_time",
        require_fields=["email", "name"],
    )
    links_repo.create(
        link_id="link-2",
        user_id="user-1",
        stripe_payment_link_id="plink_2",
        url="https://example.com",
        title="Test 2",
        description=None,
        amount=200,
        service_fee=10,
        currency="usd",
        expires_at=None,
        link_type="one_time",
        require_fields=["email", "name"],
    )
    links_repo.create(
        link_id="link-3",
        user_id="user-2",
        stripe_payment_link_id="plink_3",
        url="https://example.com",
        title="Other",
        description=None,
        amount=300,
        service_fee=15,
        currency="usd",
        expires_at=None,
        link_type="one_time",
        require_fields=["email", "name"],
    )

    user_links = links_repo.list_by_user("user-1")
    assert {item["link_id"] for item in user_links} == {"link-1", "link-2"}

    links_repo.mark_disabled("link-1")
    assert links_repo.get("link-1")["status"] == "DISABLED"

    links_repo.mark_expired("link-2")
    assert links_repo.get("link-2")["status"] == "EXPIRED"


@mock_aws
def test_subscriptions_list_by_user_and_status_updates():
    _create_tables()
    subs_repo = SubscriptionsRepository()

    subs_repo.create(
        subscription_id="sub-1",
        user_id="user-1",
        stripe_payment_link_id="plink_1",
        url="https://example.com",
        title="Sub",
        description=None,
        amount=100,
        service_fee=5,
        currency="usd",
        interval="month",
        expires_at=None,
        require_fields=["email", "name"],
    )
    subs_repo.create(
        subscription_id="sub-2",
        user_id="user-1",
        stripe_payment_link_id="plink_2",
        url="https://example.com",
        title="Sub 2",
        description=None,
        amount=200,
        service_fee=10,
        currency="usd",
        interval="month",
        expires_at=None,
        require_fields=["email", "name"],
    )
    subs_repo.create(
        subscription_id="sub-3",
        user_id="user-2",
        stripe_payment_link_id="plink_3",
        url="https://example.com",
        title="Other",
        description=None,
        amount=300,
        service_fee=15,
        currency="usd",
        interval="month",
        expires_at=None,
        require_fields=["email", "name"],
    )

    user_links = subs_repo.list_by_user("user-1")
    assert {item["subscription_id"] for item in user_links} == {"sub-1", "sub-2"}

    subs_repo.mark_disabled("sub-1")
    assert subs_repo.get("sub-1")["status"] == "DISABLED"

    subs_repo.mark_expired("sub-2")
    assert subs_repo.get("sub-2")["status"] == "EXPIRED"
