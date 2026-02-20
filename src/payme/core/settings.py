from __future__ import annotations

from pydantic import AliasChoices, Field
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
    # Backwards compatible env wiring:
    # - Terraform injects SERVICE_FEE_FIXED (cents) and SERVICE_FEE_BPS (basis points).
    # - Code uses fixed_fee (cents) + service_fee_percent (percentage).
    fixed_fee: int = Field(50, validation_alias=AliasChoices("FIXED_FEE", "SERVICE_FEE_FIXED"))
    service_fee_percent: float = Field(5.0, validation_alias=AliasChoices("SERVICE_FEE_PERCENT"))
    service_fee_bps: int | None = Field(None, validation_alias=AliasChoices("SERVICE_FEE_BPS"))
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
    ddb_table_subscriptions: str = Field(
        ...,
        validation_alias=AliasChoices(
            "DDB_TABLE_SUBSCRIPTIONS",
            "DDB_TABLE_SUBSCRIPTION_INSTANCES",
            "DDB_TABLE_SUBSCRIPTION_LINKS",
        ),
    )
    ddb_table_transactions: str

    stripe_webhook_secret: str = ""  # Webhook endpoint signing secret (whsec_...) from Stripe Dashboard

    def model_post_init(self, __context) -> None:  # type: ignore[override]
        # If SERVICE_FEE_BPS is set and SERVICE_FEE_PERCENT was not explicitly set, derive percent.
        if "service_fee_percent" not in self.__pydantic_fields_set__ and self.service_fee_bps is not None:
            self.service_fee_percent = float(self.service_fee_bps) / 100.0


settings = Settings()  # type: ignore[call-arg]
