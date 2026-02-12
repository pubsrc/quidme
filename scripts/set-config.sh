#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <dev|prod>" >&2
  exit 1
fi

ENV_NAME="$1"
if [[ "$ENV_NAME" != "dev" && "$ENV_NAME" != "prod" ]]; then
  echo "Environment must be dev or prod" >&2
  exit 1
fi

PREFIX="/payme/$ENV_NAME"
PROJECT="payme"
REGION="eu-west-2"

: "${STRIPE_SECRET:?Missing STRIPE_SECRET}"
: "${GOOGLE_CLIENT_ID:?Missing GOOGLE_CLIENT_ID}"
: "${GOOGLE_CLIENT_SECRET:?Missing GOOGLE_CLIENT_SECRET}"

SERVICE_FEE_BPS="${SERVICE_FEE_BPS:-500}"
SERVICE_FEE_FIXED="${SERVICE_FEE_FIXED:-50}"
PAYME_BASE_URL="${PAYME_BASE_URL:-https://example.com}"
PAYME_ACCOUNT_REFRESH_URL="${PAYME_ACCOUNT_REFRESH_URL:-https://example.com/refresh}"
PAYME_ACCOUNT_RETURN_URL="${PAYME_ACCOUNT_RETURN_URL:-https://example.com/return}"
COGNITO_DOMAIN_PREFIX="${COGNITO_DOMAIN_PREFIX:-payme-$ENV_NAME}"
CALLBACK_URLS="${CALLBACK_URLS:-$PAYME_BASE_URL}"
LOGOUT_URLS="${LOGOUT_URLS:-$PAYME_BASE_URL}"
EXPIRY_SCHEDULE="${EXPIRY_SCHEDULE:-rate(15 minutes)}"
CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-http://localhost:5173}"

aws --region "$REGION" secretsmanager update-secret \
  --secret-id "$PROJECT-stripe-api-key" \
  --secret-string "$STRIPE_SECRET" >/dev/null

aws --region "$REGION" secretsmanager update-secret \
  --secret-id "$PROJECT-google-oauth-pi-key" \
  --secret-string "{\"client_id\":\"$GOOGLE_CLIENT_ID\",\"client_secret\":\"$GOOGLE_CLIENT_SECRET\"}" >/dev/null

aws --region "$REGION" ssm put-parameter \
  --name "$PREFIX/service_fee_bps" \
  --type String \
  --value "$SERVICE_FEE_BPS" \
  --overwrite >/dev/null

aws --region "$REGION" ssm put-parameter \
  --name "$PREFIX/service_fee_fixed" \
  --type String \
  --value "$SERVICE_FEE_FIXED" \
  --overwrite >/dev/null

aws --region "$REGION" ssm put-parameter \
  --name "$PREFIX/payme_base_url" \
  --type String \
  --value "$PAYME_BASE_URL" \
  --overwrite >/dev/null

aws --region "$REGION" ssm put-parameter \
  --name "$PREFIX/account_refresh_url" \
  --type String \
  --value "$PAYME_ACCOUNT_REFRESH_URL" \
  --overwrite >/dev/null

aws --region "$REGION" ssm put-parameter \
  --name "$PREFIX/account_return_url" \
  --type String \
  --value "$PAYME_ACCOUNT_RETURN_URL" \
  --overwrite >/dev/null

aws --region "$REGION" ssm put-parameter \
  --name "$PREFIX/cognito_domain_prefix" \
  --type String \
  --value "$COGNITO_DOMAIN_PREFIX" \
  --overwrite >/dev/null

aws --region "$REGION" ssm put-parameter \
  --name "$PREFIX/callback_urls" \
  --type StringList \
  --value "$CALLBACK_URLS" \
  --overwrite >/dev/null

aws --region "$REGION" ssm put-parameter \
  --name "$PREFIX/logout_urls" \
  --type StringList \
  --value "$LOGOUT_URLS" \
  --overwrite >/dev/null

aws --region "$REGION" ssm put-parameter \
  --name "$PREFIX/expiry_schedule" \
  --type String \
  --value "$EXPIRY_SCHEDULE" \
  --overwrite >/dev/null

aws --region "$REGION" ssm put-parameter \
  --name "$PREFIX/cors_allowed_origins" \
  --type StringList \
  --value "$CORS_ALLOWED_ORIGINS" \
  --overwrite >/dev/null

echo "Updated secrets and SSM parameters for $ENV_NAME in $REGION"
