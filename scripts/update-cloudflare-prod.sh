#!/usr/bin/env bash
set -euo pipefail

# Updates Cloudflare DNS records for prod based on provided CNAME targets.
#
# Expected env vars:
# - CLOUDFLARE_API_TOKEN (required)
# - CLOUDFLARE_ZONE_NAME (default: quidme.uk)
# - FRONTEND_RECORD_NAME (default: @)
# - FRONTEND_CNAME_TARGET (required)
# - FRONTEND_PROXIED (default: true)
# - API_RECORD_NAME (default: api)
# - API_CNAME_TARGET (required)
# - API_PROXIED (default: false)
# - FRONTEND_ACM_VALIDATION_RECORDS_JSON (optional; output from Terraform `frontend_acm_validation_records`)
# - API_ACM_VALIDATION_RECORDS_JSON (optional; output from Terraform `api_acm_validation_records`)

# -----------------------------------------------------------------------------
# Configuration (set these at the top, then run the script)
# -----------------------------------------------------------------------------

# Required: Cloudflare API token.
: "${CLOUDFLARE_API_TOKEN:=}"

# Optional: where to read Terraform outputs from (used to auto-fill targets).
# Default resolves relative to the repo root, not the current working directory.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
: "${TERRAFORM_ENV_DIR:=${REPO_ROOT}/terraform/environments/prod}"

# If a relative path is provided, resolve it relative to repo root for stability.
if [[ "${TERRAFORM_ENV_DIR}" != /* ]]; then
  TERRAFORM_ENV_DIR="${REPO_ROOT}/${TERRAFORM_ENV_DIR}"
fi

# Optional: zone name (root domain) in Cloudflare.
: "${CLOUDFLARE_ZONE_NAME:=quidme.uk}"

# Frontend record:
# - FRONTEND_RECORD_NAME: record name within the zone. Use "@" for the zone apex.
# - FRONTEND_CNAME_TARGET: CloudFront distribution domain name (e.g. d123.cloudfront.net).
# - FRONTEND_PROXIED: Cloudflare proxy toggle (true/false).
: "${FRONTEND_RECORD_NAME:=@}"
: "${FRONTEND_CNAME_TARGET:=}"
: "${FRONTEND_PROXIED:=true}"

# API record:
# - API_RECORD_NAME: record name within the zone (e.g. "api").
# - API_CNAME_TARGET: API Gateway custom domain target (looks like `xxxxx.execute-api...`).
# - API_PROXIED: should usually be false for API Gateway custom domains.
: "${API_RECORD_NAME:=api}"
: "${API_CNAME_TARGET:=}"
: "${API_PROXIED:=false}"

# Optional: ACM validation records exported from Terraform outputs (JSON arrays).
# These are created as proxied=false.
: "${FRONTEND_ACM_VALIDATION_RECORDS_JSON:=[]}"
: "${API_ACM_VALIDATION_RECORDS_JSON:=[]}"

# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------

if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  echo "Missing CLOUDFLARE_API_TOKEN. Export it in your shell environment." >&2
  exit 1
fi

terraform_output() {
  local name="$1"
  terraform -chdir="${TERRAFORM_ENV_DIR}" output -raw "$name"
}

terraform_output_json() {
  local name="$1"
  terraform -chdir="${TERRAFORM_ENV_DIR}" output -json "$name"
}

if [[ -z "${FRONTEND_CNAME_TARGET:-}" || -z "${API_CNAME_TARGET:-}" ]]; then
  if [[ -d "${TERRAFORM_ENV_DIR}" ]] && command -v terraform >/dev/null 2>&1; then
    # Auto-fill from Terraform outputs (unless explicitly provided by env).
    if [[ -z "${FRONTEND_CNAME_TARGET:-}" ]]; then
      FRONTEND_CNAME_TARGET="$(terraform_output frontend_cloudfront_domain_name 2>/dev/null || true)"
    fi
    if [[ -z "${API_CNAME_TARGET:-}" ]]; then
      API_CNAME_TARGET="$(terraform_output api_custom_domain_target 2>/dev/null || true)"
    fi

    # Also auto-fill ACM validation records if they still have their defaults.
    if [[ "${FRONTEND_ACM_VALIDATION_RECORDS_JSON:-}" == "[]" ]]; then
      FRONTEND_ACM_VALIDATION_RECORDS_JSON="$(terraform_output_json frontend_acm_validation_records 2>/dev/null || echo "[]")"
    fi
    if [[ "${API_ACM_VALIDATION_RECORDS_JSON:-}" == "[]" ]]; then
      API_ACM_VALIDATION_RECORDS_JSON="$(terraform_output_json api_acm_validation_records 2>/dev/null || echo "[]")"
    fi
  fi
fi

ZONE_NAME="${CLOUDFLARE_ZONE_NAME}"

FRONTEND_RECORD_NAME="${FRONTEND_RECORD_NAME}"
FRONTEND_CNAME_TARGET="${FRONTEND_CNAME_TARGET}"
FRONTEND_PROXIED="${FRONTEND_PROXIED}"

API_RECORD_NAME="${API_RECORD_NAME}"
API_CNAME_TARGET="${API_CNAME_TARGET}"
API_PROXIED="${API_PROXIED}"

FRONTEND_ACM_VALIDATION_RECORDS_JSON="${FRONTEND_ACM_VALIDATION_RECORDS_JSON}"
API_ACM_VALIDATION_RECORDS_JSON="${API_ACM_VALIDATION_RECORDS_JSON}"

if [[ -z "$FRONTEND_CNAME_TARGET" ]]; then
  echo "Missing FRONTEND_CNAME_TARGET." >&2
  echo "Set it explicitly, or ensure terraform outputs are available at TERRAFORM_ENV_DIR='${TERRAFORM_ENV_DIR}'." >&2
  exit 1
fi
if [[ -z "$API_CNAME_TARGET" ]]; then
  echo "Missing API_CNAME_TARGET." >&2
  echo "Set it explicitly, or ensure terraform outputs are available at TERRAFORM_ENV_DIR='${TERRAFORM_ENV_DIR}'." >&2
  exit 1
fi

auth_header=("Authorization: Bearer ${CLOUDFLARE_API_TOKEN}")
json_header=("Content-Type: application/json")

cf_get() {
  local url="$1"
  curl -fsS -H "${auth_header[@]}" "$url"
}

cf_put() {
  local url="$1"
  local body="$2"
  curl -fsS -X PUT -H "${auth_header[@]}" -H "${json_header[@]}" --data "$body" "$url" >/dev/null
}

cf_post() {
  local url="$1"
  local body="$2"
  curl -fsS -X POST -H "${auth_header[@]}" -H "${json_header[@]}" --data "$body" "$url" >/dev/null
}

zone_id="$(
  cf_get "https://api.cloudflare.com/client/v4/zones?name=${ZONE_NAME}" \
    | jq -r '.result[0].id // empty'
)"

if [[ -z "$zone_id" ]]; then
  echo "Failed to resolve Cloudflare zone id for ${ZONE_NAME}" >&2
  exit 1
fi

fqdn_for() {
  local name="$1"
  if [[ "$name" == "@" ]]; then
    echo "$ZONE_NAME"
  else
    echo "${name}.${ZONE_NAME}"
  fi
}

trim_trailing_dot() {
  local s="$1"
  echo "${s%.}"
}

upsert_record_fqdn() {
  local record_type="$1"
  local fqdn="$2"
  local content="$3"
  local proxied="$4"

  fqdn="$(trim_trailing_dot "$fqdn")"
  content="$(trim_trailing_dot "$content")"

  local record_id
  record_id="$(
    cf_get "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records?type=${record_type}&name=${fqdn}" \
      | jq -r '.result[0].id // empty'
  )"

  local body
  body="$(jq -n \
    --arg type "$record_type" \
    --arg name "$fqdn" \
    --arg content "$content" \
    --argjson ttl 1 \
    --argjson proxied "$proxied" \
    '{type:$type,name:$name,content:$content,ttl:$ttl,proxied:$proxied}')"

  if [[ -n "$record_id" ]]; then
    cf_put "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records/${record_id}" "$body"
    echo "Updated ${record_type} ${fqdn} -> ${content} (proxied=${proxied})"
  else
    cf_post "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records" "$body"
    echo "Created ${record_type} ${fqdn} -> ${content} (proxied=${proxied})"
  fi
}

upsert_record_fqdn "CNAME" "$(fqdn_for "$FRONTEND_RECORD_NAME")" "$FRONTEND_CNAME_TARGET" "$FRONTEND_PROXIED"
upsert_record_fqdn "CNAME" "$(fqdn_for "$API_RECORD_NAME")" "$API_CNAME_TARGET" "$API_PROXIED"

echo "Upserting ACM validation records (proxied=false)..."

echo "$FRONTEND_ACM_VALIDATION_RECORDS_JSON" \
  | jq -c '.[]?' \
  | while read -r rec; do
      name="$(jq -r '.name' <<<"$rec")"
      type="$(jq -r '.type' <<<"$rec")"
      value="$(jq -r '.value' <<<"$rec")"
      [[ -z "$name" || -z "$type" || -z "$value" ]] && continue
      upsert_record_fqdn "$type" "$name" "$value" "false"
    done

echo "$API_ACM_VALIDATION_RECORDS_JSON" \
  | jq -c '.[]?' \
  | while read -r rec; do
      name="$(jq -r '.name' <<<"$rec")"
      type="$(jq -r '.type' <<<"$rec")"
      value="$(jq -r '.value' <<<"$rec")"
      [[ -z "$name" || -z "$type" || -z "$value" ]] && continue
      upsert_record_fqdn "$type" "$name" "$value" "false"
    done
