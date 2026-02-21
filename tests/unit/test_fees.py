from payme.services.fees import (
    amount_with_fee,
    amount_with_subscription_fee,
    earnings_from_payment,
    subtract_fees,
    subtract_service_fee,
)


def test_amount_with_fee_formula():
    # Fixed-fee tiers only (service percent ignored). amount=100 (<=10) => fee=40.
    total, service_fee_percent, stripe_fee_percent, service_fee_cents = amount_with_fee(
        100, currency="usd", stripe_fee_percent=0.0
    )
    assert total == 140
    assert service_fee_percent > 0
    assert stripe_fee_percent == 0.0
    assert service_fee_cents == 40


def test_amount_with_fee_stripe_percent():
    total, service_fee_percent, stripe_fee_percent, service_fee_cents = amount_with_fee(
        1000, currency="usd", stripe_fee_percent=2.9
    )
    # amount=1000 (<=10) => fee=40; total = (1040)/(1-0.029)=1071.06 -> 1071
    assert total == 1071
    assert service_fee_percent > 0
    assert stripe_fee_percent == 2.9
    assert service_fee_cents == 40


def test_amount_with_subscription_fee():
    total, service_fee_percent, stripe_fee_percent = amount_with_subscription_fee(
        500, currency="usd", stripe_fee_percent=0.0
    )
    # amount=500 (<=10) => fee=40
    assert total == 540
    assert service_fee_percent > 0
    assert stripe_fee_percent == 0.0


def test_subtract_fees():
    assert subtract_fees(100, 55) == 45
    assert subtract_fees(40, 55) == 0


def test_subtract_service_fee_alias():
    assert subtract_service_fee(100, 55) == 45


def test_earnings_from_payment_with_known_service_fee():
    # known_service_fee bypasses service pct. fixed is still subtracted from total paid.
    earnings = earnings_from_payment(
        140, known_service_fee_cents=40, fixed_fee=0, stripe_fee_percent=0.0
    )
    assert earnings == 100


def test_amount_with_fee_rejects_percent_ge_100():
    try:
        amount_with_fee(100, currency="usd", service_fee_percent=50, stripe_fee_percent=100)
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
