# E2E tests

- Default: `pytest` runs all tests **except** those marked `e2e_stripe` (see `addopts` in pyproject.toml).
- Health check in `test_health.py` runs by default.

## Stripe E2E (opt-in only)

`test_stripe_e2e.py` calls the **real Stripe API** (test mode) and cleans up.

**Requirements**

- `STRIPE_SECRET` in `.env` (pydantic-settings reads it as `stripe_secret`). Use a test secret from Stripe Dashboard → Developers → API keys.

**Run**

```bash
pytest -m e2e_stripe -v
```

**What they do**

- **test_connect_account_and_payment_link_created_in_stripe**: Creates a Connect Express account and a one-time payment link via `StripeService`, asserts both exist in Stripe, then disables the link.
- **test_subscription_link_created_in_stripe**: Creates a subscription payment link via `StripeService.create_payment_link_subscription`, asserts it exists with correct metadata and recurring price, then disables the link.

**Identifying test links in Stripe:** With `PAYME_ENV=test`, links use product name `TEST_YYYY_MM_DD_HH_MM` (UTC) in Stripe.
