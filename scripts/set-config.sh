#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <dev|prod> [env-file]" >&2
  exit 1
fi

ENV_NAME="$1"
if [[ "$ENV_NAME" != "dev" && "$ENV_NAME" != "prod" ]]; then
  echo "Environment must be dev or prod" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${2:-$ROOT_DIR/.env.$ENV_NAME}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file not found: $ENV_FILE" >&2
  exit 1
fi
FRONTEND_ENV_FILE="$ROOT_DIR/frontend/.env.$ENV_NAME"

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

# If frontend env exists, load VITE_* values from there too so frontend
# runtime config can be synced to SSM by a single command.
if [[ -f "$FRONTEND_ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "$FRONTEND_ENV_FILE"
  set +a
fi

PREFIX="/payme/$ENV_NAME"
PROJECT="payme"
REGION="${AWS_REGION:-eu-west-2}"

: "${STRIPE_SECRET:?Missing STRIPE_SECRET}"
: "${STRIPE_WEBHOOK_SECRET:?Missing STRIPE_WEBHOOK_SECRET}"
: "${GOOGLE_CLIENT_ID:?Missing GOOGLE_CLIENT_ID}"
: "${GOOGLE_CLIENT_SECRET:?Missing GOOGLE_CLIENT_SECRET}"

SERVICE_FEE_PERCENT="${SERVICE_FEE_PERCENT:-2}"
SERVICE_FEE_BPS="${SERVICE_FEE_BPS:-$(awk "BEGIN { printf \"%.0f\", ${SERVICE_FEE_PERCENT} * 100 }")}"
SERVICE_FEE_FIXED="${SERVICE_FEE_FIXED:-${FIXED_FEE:-50}}"
PAYME_BASE_URL="${PAYME_BASE_URL:-https://example.com}"
PAYME_ACCOUNT_REFRESH_URL="${PAYME_ACCOUNT_REFRESH_URL:-https://example.com/refresh}"
PAYME_ACCOUNT_RETURN_URL="${PAYME_ACCOUNT_RETURN_URL:-https://example.com/return}"
COGNITO_DOMAIN_PREFIX="${COGNITO_DOMAIN_PREFIX:-payme-$ENV_NAME}"
CALLBACK_URLS="${CALLBACK_URLS:-$PAYME_BASE_URL}"
LOGOUT_URLS="${LOGOUT_URLS:-$PAYME_BASE_URL}"
EXPIRY_SCHEDULE="${EXPIRY_SCHEDULE:-rate(15 minutes)}"
# Best-practice default: allow the frontend origin (rather than "*") so CORS behaves
# predictably with auth and future cookie-based flows.
CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-$PAYME_BASE_URL}"

COGNITO_REGION="${COGNITO_REGION:-$REGION}"
COGNITO_USER_POOL_ID="${COGNITO_USER_POOL_ID:-}"
COGNITO_APP_CLIENT_ID="${COGNITO_APP_CLIENT_ID:-}"
COGNITO_REDIRECT_URI="${COGNITO_REDIRECT_URI:-$PAYME_BASE_URL/callback}"
DEFAULT_COUNTRY="${DEFAULT_COUNTRY:-GB}"
PAYME_ENV="${PAYME_ENV:-$ENV_NAME}"
STRIPE_FEE_PERCENT="${STRIPE_FEE_PERCENT:-2}"

DDB_TABLE_USERS="${DDB_TABLE_USERS:-payme-users}"
DDB_TABLE_USER_IDENTITIES="${DDB_TABLE_USER_IDENTITIES:-payme-user-identities}"
DDB_TABLE_PAYMENT_LINKS="${DDB_TABLE_PAYMENT_LINKS:-payme-payment-links}"
DDB_TABLE_SUBSCRIPTION_LINKS="${DDB_TABLE_SUBSCRIPTION_LINKS:-payme-subscription-links}"
DDB_TABLE_USER_ACCOUNTS="${DDB_TABLE_USER_ACCOUNTS:-payme-user-accounts}"
DDB_TABLE_TRANSACTIONS="${DDB_TABLE_TRANSACTIONS:-payme-transactions}"
DDB_TABLE_STRIPE_ACCOUNTS="${DDB_TABLE_STRIPE_ACCOUNTS:-payme-stripe-accounts}"

VITE_API_BASE_URL="${VITE_API_BASE_URL:-$PAYME_BASE_URL}"
VITE_COGNITO_USER_POOL_ID="${VITE_COGNITO_USER_POOL_ID:-$COGNITO_USER_POOL_ID}"
VITE_COGNITO_USER_POOL_CLIENT_ID="${VITE_COGNITO_USER_POOL_CLIENT_ID:-$COGNITO_APP_CLIENT_ID}"
VITE_COGNITO_REGION="${VITE_COGNITO_REGION:-$COGNITO_REGION}"
VITE_COGNITO_OAUTH_DOMAIN="${VITE_COGNITO_OAUTH_DOMAIN:-${COGNITO_DOMAIN_PREFIX}.auth.${COGNITO_REGION}.amazoncognito.com}"
VITE_OAUTH_REDIRECT_SIGN_IN="${VITE_OAUTH_REDIRECT_SIGN_IN:-$COGNITO_REDIRECT_URI}"
VITE_OAUTH_REDIRECT_SIGN_OUT="${VITE_OAUTH_REDIRECT_SIGN_OUT:-$PAYME_BASE_URL}"

put_ssm() {
  local name="$1"
  local value="$2"
  local type="${3:-String}"
  aws --region "$REGION" ssm put-parameter \
    --name "$PREFIX/$name" \
    --type "$type" \
    --value "$value" \
    --overwrite >/dev/null
}

aws --region "$REGION" secretsmanager update-secret \
  --secret-id "$PROJECT-stripe-api-key" \
  --secret-string "$STRIPE_SECRET" >/dev/null

aws --region "$REGION" secretsmanager update-secret \
  --secret-id "$PROJECT-stripe-webhook-secret" \
  --secret-string "$STRIPE_WEBHOOK_SECRET" >/dev/null

aws --region "$REGION" secretsmanager update-secret \
  --secret-id "$PROJECT-google-oauth-pi-key" \
  --secret-string "{\"client_id\":\"$GOOGLE_CLIENT_ID\",\"client_secret\":\"$GOOGLE_CLIENT_SECRET\"}" >/dev/null

put_ssm "service_fee_bps" "$SERVICE_FEE_BPS"
put_ssm "service_fee_fixed" "$SERVICE_FEE_FIXED"
put_ssm "payme_base_url" "$PAYME_BASE_URL"
put_ssm "account_refresh_url" "$PAYME_ACCOUNT_REFRESH_URL"
put_ssm "account_return_url" "$PAYME_ACCOUNT_RETURN_URL"
put_ssm "cognito_domain_prefix" "$COGNITO_DOMAIN_PREFIX"
put_ssm "callback_urls" "$CALLBACK_URLS" "StringList"
put_ssm "logout_urls" "$LOGOUT_URLS" "StringList"
put_ssm "expiry_schedule" "$EXPIRY_SCHEDULE"
put_ssm "cors_allowed_origins" "$CORS_ALLOWED_ORIGINS" "StringList"

# Additional app config from env file.
put_ssm "google_client_id" "$GOOGLE_CLIENT_ID"
put_ssm "cognito_region" "$COGNITO_REGION"
put_ssm "cognito_user_pool_id" "$COGNITO_USER_POOL_ID"
put_ssm "cognito_app_client_id" "$COGNITO_APP_CLIENT_ID"
put_ssm "cognito_redirect_uri" "$COGNITO_REDIRECT_URI"
put_ssm "default_country" "$DEFAULT_COUNTRY"
put_ssm "payme_env" "$PAYME_ENV"
put_ssm "fixed_fee" "$SERVICE_FEE_FIXED"
put_ssm "service_fee_percent" "$SERVICE_FEE_PERCENT"
put_ssm "stripe_fee_percent" "$STRIPE_FEE_PERCENT"
put_ssm "ddb_table_users" "$DDB_TABLE_USERS"
put_ssm "ddb_table_user_identities" "$DDB_TABLE_USER_IDENTITIES"
put_ssm "ddb_table_payment_links" "$DDB_TABLE_PAYMENT_LINKS"
put_ssm "ddb_table_subscription_links" "$DDB_TABLE_SUBSCRIPTION_LINKS"
put_ssm "ddb_table_user_accounts" "$DDB_TABLE_USER_ACCOUNTS"
put_ssm "ddb_table_transactions" "$DDB_TABLE_TRANSACTIONS"
put_ssm "ddb_table_stripe_accounts" "$DDB_TABLE_STRIPE_ACCOUNTS"
put_ssm "vite_api_base_url" "$VITE_API_BASE_URL"
put_ssm "vite_cognito_user_pool_id" "$VITE_COGNITO_USER_POOL_ID"
put_ssm "vite_cognito_user_pool_client_id" "$VITE_COGNITO_USER_POOL_CLIENT_ID"
put_ssm "vite_cognito_region" "$VITE_COGNITO_REGION"
put_ssm "vite_cognito_oauth_domain" "$VITE_COGNITO_OAUTH_DOMAIN"
put_ssm "vite_oauth_redirect_sign_in" "$VITE_OAUTH_REDIRECT_SIGN_IN"
put_ssm "vite_oauth_redirect_sign_out" "$VITE_OAUTH_REDIRECT_SIGN_OUT"

echo "Updated secrets and SSM parameters for $ENV_NAME in $REGION using $ENV_FILE (and $FRONTEND_ENV_FILE when present)"
