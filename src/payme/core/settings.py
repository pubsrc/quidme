from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    stripe_secret: str
    # Fee model: fixed_fee (cents) + service_fee_percent (platform) + stripe_fee_percent (Stripe)
    # total = (amount + fixed_fee) / (1 - (service_fee_percent + stripe_fee_percent) / 100)
    fixed_fee: int = 50  # Fixed amount in cents added to customer total
    service_fee_percent: float = 5.0  # Platform fee as % of total (application_fee)
    stripe_fee_percent: float = 0.0  # Stripe fee as % of total

    cognito_region: str = "eu-west-2"
    cognito_user_pool_id: str
    cognito_app_client_id: str

    payme_env: str = "local"
    payme_base_url: str
    payme_account_refresh_url: str
    payme_account_return_url: str
    default_country: str = "GB"

    cors_allowed_origins: str = "*"

    ddb_table_users: str
    ddb_table_user_identities: str
    ddb_table_stripe_accounts: str
    ddb_table_payment_links: str
    ddb_table_subscription_links: str
    ddb_table_transactions: str

    stripe_webhook_secret: str = ""  # Webhook endpoint signing secret (whsec_...) from Stripe Dashboard


settings = Settings()  # type: ignore[call-arg]
