import os

# Tests must be deterministic and must not depend on a developer's local `.env`.
# Provide a minimal, stable environment for Settings() to boot.
os.environ.setdefault("STRIPE_SECRET", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")

# Fee defaults used across unit tests.
os.environ.setdefault("FIXED_FEE", "50")
os.environ.setdefault("SERVICE_FEE_PERCENT", "5")
os.environ.setdefault("STRIPE_FEE_PERCENT", "0")

os.environ.setdefault("COGNITO_REGION", "eu-west-2")
os.environ.setdefault("COGNITO_USER_POOL_ID", "eu-west-2_dummy")
os.environ.setdefault("COGNITO_APP_CLIENT_ID", "dummy")

os.environ.setdefault("PAYME_ENV", "test")
os.environ.setdefault("PAYME_BASE_URL", "https://example.com")
os.environ.setdefault("PAYME_ACCOUNT_REFRESH_URL", "https://example.com/refresh")
os.environ.setdefault("PAYME_ACCOUNT_RETURN_URL", "https://example.com/return")

os.environ.setdefault("DDB_TABLE_USERS", "payme-users")
os.environ.setdefault("DDB_TABLE_USER_IDENTITIES", "payme-user-identities")
os.environ.setdefault("DDB_TABLE_STRIPE_ACCOUNTS", "payme-stripe-accounts")
os.environ.setdefault("DDB_TABLE_PAYMENT_LINKS", "payme-payment-links")
os.environ.setdefault("DDB_TABLE_SUBSCRIPTION_LINKS", "payme-subscription-links")
os.environ.setdefault("DDB_TABLE_SUBSCRIPTIONS", "payme-subscriptions")
os.environ.setdefault("DDB_TABLE_TRANSACTIONS", "payme-transactions")

os.environ.setdefault("CORS_ALLOWED_ORIGINS", "*")
