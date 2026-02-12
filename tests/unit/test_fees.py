from payme.services.fees import (
    amount_with_fee,
    amount_with_subscription_fee,
    earnings_from_payment,
    subtract_fees,
    subtract_service_fee,
)


def test_amount_with_fee_formula():
    # total = (amount + fixed_fee) / (1 - (service_fee_percent + stripe_fee_percent)/100)
    # amount=100, fixed_fee=50, service_fee=5%, stripe_fee=0% -> total = 150/0.95 = 157.89 -> 158
    total, service_fee_percent, stripe_fee_percent, service_fee_cents = amount_with_fee(
        100, fixed_fee=50, service_fee_percent=5.0, stripe_fee_percent=0.0
    )
    assert total == 158
    assert service_fee_percent == 5.0
    assert stripe_fee_percent == 0.0
    assert service_fee_cents == 8  # 158 * 0.05


def test_amount_with_fee_stripe_percent():
    total, service_fee_percent, stripe_fee_percent, service_fee_cents = amount_with_fee(
        1000, fixed_fee=0, service_fee_percent=5.0, stripe_fee_percent=2.9
    )
    # total = 1000 / (1 - 0.079) = 1000/0.921 ~ 1085.78 -> 1086
    assert total == 1086
    assert service_fee_percent == 5.0
    assert stripe_fee_percent == 2.9
    assert service_fee_cents == 54  # 1086 * 0.05


def test_amount_with_subscription_fee():
    total, service_fee_percent, stripe_fee_percent = amount_with_subscription_fee(
        500, fixed_fee=50, service_fee_percent=5.0, stripe_fee_percent=0.0
    )
    # (500+50)/0.95 = 578.95 -> 579
    assert total == 579
    assert service_fee_percent == 5.0
    assert stripe_fee_percent == 0.0


def test_subtract_fees():
    assert subtract_fees(100, 55) == 45
    assert subtract_fees(40, 55) == 0


def test_subtract_service_fee_alias():
    assert subtract_service_fee(100, 55) == 45


def test_earnings_from_payment_with_known_service_fee():
    # total_paid=158, fixed=50, stripe=0, known_service_fee=8 -> earnings = 158 - 50 - 8 = 100
    earnings = earnings_from_payment(
        158, known_service_fee_cents=8, fixed_fee=50, stripe_fee_percent=0.0
    )
    assert earnings == 100


def test_amount_with_fee_rejects_percent_ge_100():
    try:
        amount_with_fee(100, fixed_fee=0, service_fee_percent=50, stripe_fee_percent=50)
    except ValueError as exc:
        assert "100" in str(exc)
    else:
        assert False, "Expected ValueError"


def test_subtract_fees_rejects_negative_amount():
    try:
        subtract_fees(-1, 1)
    except ValueError as exc:
        assert "amount" in str(exc)
    else:
        assert False, "Expected ValueError"


def test_subtract_fees_rejects_negative_fee():
    try:
        subtract_fees(100, -1)
    except ValueError as exc:
        assert "non-negative" in str(exc)
    else:
        assert False, "Expected ValueError"
