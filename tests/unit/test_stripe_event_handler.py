"""Unit tests for Stripe event handling: payment_intent.succeeded, invoice.paid.

Assert that earnings are updated in both payment/subscription links and in the
stripe_accounts table (DynamoDB).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from payme.core.settings import settings
from payme.services.stripe_event_handler import (
    handle_invoice_paid,
    handle_payment_succeeded,
)


def _payment_intent_succeeded_event(
    user_id: str = "user-1",
    link_id: str = "link-1",
    amount: int = 1000,
    currency: str = "gbp",
    payment_intent_id: str = "pi_xxx",
    application_fee_amount: int | None = None,
) -> dict:
    """Minimal payment_intent.succeeded event payload."""
    return {
        "object": {
            "id": payment_intent_id,
            "amount_received": amount,
            "amount": amount,
            "currency": currency,
            "created": 1700000000,
            "application_fee_amount": application_fee_amount,
            "metadata": {"user_id": user_id, "link_id": link_id},
            "charges": {"data": []},
        }
    }


def _invoice_paid_event(
    user_id: str = "user-1",
    link_id: str = "sub-1",
    amount: int = 2000,
    currency: str = "usd",
    invoice_id: str = "in_yyy",
    payment_intent_id: str = "pi_zzz",
) -> dict:
    """Minimal invoice.paid event payload (subscription). Uses lines.data[0].metadata for user_id/link_id so extraction does not call Stripe."""
    return {
        "object": {
            "id": invoice_id,
            "amount_paid": amount,
            "currency": currency,
            "created": 1700000000,
            "customer_email": "customer@example.com",
            "payment_intent": {"id": payment_intent_id} if payment_intent_id else None,
            "subscription": "sub_stripe_1",
            "lines": {
                "data": [
                    {"metadata": {"user_id": user_id, "link_id": link_id}},
                ]
            },
        }
    }


@patch("payme.services.stripe_event_handler.StripeAccountRepository")
@patch("payme.services.stripe_event_handler.PaymentLinksRepository")
@patch("payme.services.stripe_event_handler.TransactionsRepository")
def test_handle_payment_succeeded_updates_payment_link_and_stripe_account_earnings(
    mock_tx_repo_cls: MagicMock,
    mock_links_repo_cls: MagicMock,
    mock_account_repo_cls: MagicMock,
) -> None:
    """Payment intent succeeded: earnings added to payment link and to stripe_accounts (DynamoDB)."""
    mock_links_repo = MagicMock()
    mock_links_repo.get.return_value = {"link_id": "link-1", "service_fee": 55}
    mock_links_repo_cls.return_value = mock_links_repo

    mock_tx_repo = MagicMock()
    mock_tx_repo.get_by_payment_intent_id.return_value = None
    mock_tx_repo_cls.return_value = mock_tx_repo

    data = _payment_intent_succeeded_event(user_id="u1", link_id="link-1", amount=1000, currency="gbp")
    result = handle_payment_succeeded("payment_intent.succeeded", data, account_id=None)

    assert result is True
    mock_links_repo.add_payment_result.assert_called_once()
    call_args = mock_links_repo.add_payment_result.call_args[0]
    assert call_args[0] == "link-1"
    earnings = call_args[1]
    total_amount = call_args[2]
    assert total_amount == 1000
    assert earnings == 1000 - 55 - settings.fixed_fee  # total_paid - service_fee - fixed_fee

    mock_account_repo_cls.return_value.add_earnings.assert_called_once()
    acc_call = mock_account_repo_cls.return_value.add_earnings.call_args[0]
    assert acc_call[0] == "u1"
    assert acc_call[1] == earnings
    assert acc_call[2] == "gbp"


@patch("payme.services.stripe_event_handler.StripeAccountRepository")
@patch("payme.services.stripe_event_handler.PaymentLinksRepository")
@patch("payme.services.stripe_event_handler.TransactionsRepository")
def test_handle_payment_succeeded_connect_account_still_updates_earnings(
    mock_tx_repo_cls: MagicMock,
    mock_links_repo_cls: MagicMock,
    mock_account_repo_cls: MagicMock,
) -> None:
    """With connected account (account_id set), earnings still added to link and stripe_accounts."""
    mock_links_repo = MagicMock()
    mock_links_repo.get.return_value = {"link_id": "link-2", "service_fee": 0}
    mock_links_repo_cls.return_value = mock_links_repo

    mock_tx_repo = MagicMock()
    mock_tx_repo.get_by_payment_intent_id.return_value = None
    mock_tx_repo_cls.return_value = mock_tx_repo

    data = _payment_intent_succeeded_event(
        user_id="u2", link_id="link-2", amount=5000, currency="usd", application_fee_amount=100
    )
    result = handle_payment_succeeded("payment_intent.succeeded", data, account_id="acct_connected")

    assert result is True
    mock_links_repo.add_payment_result.assert_called_once()
    call_args = mock_links_repo.add_payment_result.call_args[0]
    assert call_args[0] == "link-2"
    assert call_args[2] == 5000
    earnings = call_args[1]
    assert earnings == 5000 - 100 - settings.fixed_fee  # total_paid - application_fee - fixed_fee

    mock_account_repo_cls.return_value.add_earnings.assert_called_once()
    acc_call = mock_account_repo_cls.return_value.add_earnings.call_args[0]
    assert acc_call[0] == "u2"
    assert acc_call[1] == earnings
    assert acc_call[2] == "usd"


@patch("payme.services.stripe_event_handler.StripeAccountRepository")
@patch("payme.services.stripe_event_handler.SubscriptionsRepository")
@patch("payme.services.stripe_event_handler.TransactionsRepository")
def test_handle_invoice_paid_updates_subscription_link_and_stripe_account_earnings(
    mock_tx_repo_cls: MagicMock,
    mock_subs_repo_cls: MagicMock,
    mock_account_repo_cls: MagicMock,
) -> None:
    """Invoice paid: earnings added to subscription link and to stripe_accounts (DynamoDB)."""
    mock_subs_repo = MagicMock()
    mock_subs_repo.get.return_value = {"subscription_id": "sub-1", "service_fee": 100}
    mock_subs_repo_cls.return_value = mock_subs_repo

    mock_tx_repo = MagicMock()
    mock_tx_repo.get_by_payment_intent_id.return_value = None
    mock_tx_repo_cls.return_value = mock_tx_repo

    data = _invoice_paid_event(user_id="u3", link_id="sub-1", amount=3000, currency="gbp")
    result = handle_invoice_paid("invoice.paid", data, account_id=None)

    assert result is True
    mock_subs_repo.add_payment_result.assert_called_once()
    call_args = mock_subs_repo.add_payment_result.call_args[0]
    assert call_args[0] == "sub-1"
    earnings = call_args[1]
    total_amount = call_args[2]
    assert total_amount == 3000
    assert earnings == 3000 - 100 - settings.fixed_fee

    mock_account_repo_cls.return_value.add_earnings.assert_called_once()
    acc_call = mock_account_repo_cls.return_value.add_earnings.call_args[0]
    assert acc_call[0] == "u3"
    assert acc_call[1] == earnings
    assert acc_call[2] == "gbp"


@patch("payme.services.stripe_event_handler.StripeAccountRepository")
@patch("payme.services.stripe_event_handler.SubscriptionsRepository")
@patch("payme.services.stripe_event_handler.TransactionsRepository")
def test_handle_invoice_paid_zero_earnings_does_not_call_add_earnings(
    mock_tx_repo_cls: MagicMock,
    mock_subs_repo_cls: MagicMock,
    mock_account_repo_cls: MagicMock,
) -> None:
    """When earnings are 0 (e.g. full fee), add_earnings is not called on stripe account."""
    mock_subs_repo = MagicMock()
    mock_subs_repo.get.return_value = {"subscription_id": "sub-1", "service_fee": 500}
    mock_subs_repo_cls.return_value = mock_subs_repo

    mock_tx_repo = MagicMock()
    mock_tx_repo.get_by_payment_intent_id.return_value = None
    mock_tx_repo_cls.return_value = mock_tx_repo

    data = _invoice_paid_event(user_id="u4", link_id="sub-1", amount=500, currency="usd")
    result = handle_invoice_paid("invoice.paid", data, account_id=None)

    assert result is True
    mock_subs_repo.add_payment_result.assert_called_once()
    # earnings = 500 - 500 - fixed_fee < 0 -> 0
    mock_account_repo_cls.return_value.add_earnings.assert_not_called()


@patch("payme.services.stripe_event_handler.StripeAccountRepository")
@patch("payme.services.stripe_event_handler.PaymentLinksRepository")
@patch("payme.services.stripe_event_handler.TransactionsRepository")
def test_handle_payment_succeeded_missing_metadata_returns_false(
    mock_tx_repo_cls: MagicMock,
    mock_links_repo_cls: MagicMock,
    mock_account_repo_cls: MagicMock,
) -> None:
    """When metadata lacks user_id/link_id, handler returns False and does not update earnings."""
    data = {
        "object": {
            "id": "pi_xxx",
            "amount_received": 1000,
            "currency": "gbp",
            "metadata": {},
        }
    }
    result = handle_payment_succeeded("payment_intent.succeeded", data)

    assert result is False
    mock_links_repo_cls.return_value.add_payment_result.assert_not_called()
    mock_account_repo_cls.return_value.add_earnings.assert_not_called()
