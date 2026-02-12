# payme

Payme is a small Stripe Connect platform built with FastAPI + Mangum and deployed on AWS Lambda + API Gateway. It supports:

1. One-time payment links
2. Subscription links
3. Paginated transaction views
4. Refunds

Local dev reads env vars from `.env`. CI/CD injects env vars during deploy.

## Local dev

1. `uv pip install -e ".[dev]"`
2. Copy `.env.example` to `.env` and fill values.
3. `uv run python -m uvicorn payme.api.main:app --reload`

## Tests

`pytest`

## Terraform

Environment stacks follow the same pattern as opedia:

1. `terraform/environments/dev`
2. `terraform/environments/prod`

Each env uses the shared modules in `terraform/modules`.

### Secrets and config

Terraform now creates:
1. Secrets in Secrets Manager with placeholder values (update after first apply).
2. Config values in SSM Parameter Store with defaults (update after first apply).

Lambdas read these values at deploy time via Terraform data sources and inject them as environment variables.
