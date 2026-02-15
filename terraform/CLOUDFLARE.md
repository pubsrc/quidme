# Cloudflare DNS Management (Prod)

We no longer manage Cloudflare DNS records with the Terraform Cloudflare provider.

## Why

- Cloudflare provider state schema drift can break Terraform runs (state decode errors).
- DNS changes are better handled as an explicit, manual/controlled action.

## What Terraform Manages Now

- **AWS resources** (API Gateway, Lambda, Cognito, DynamoDB, CloudFront, S3, ACM).
- **ACM certificates** are still created in Terraform (when you don't provide an existing ARN), but
  **DNS validation records are not created automatically**.
  Terraform outputs the required ACM DNS validation records for you to create in Cloudflare.

## How To Update Cloudflare (Prod)

Use the GitHub Actions workflow:

- `Update Cloudflare DNS - Prod` (`.github/workflows/update-cloudflare-prod.yml`)

It reads Terraform outputs from `terraform/environments/prod` and upserts:

- `quidme.uk` CNAME → CloudFront distribution domain
- `api.quidme.uk` CNAME → API Gateway custom domain target
- ACM DNS validation records for:
  - `quidme.uk` (CloudFront/ACM in `us-east-1`)
  - `api.quidme.uk` (ACM in `eu-west-2`)

## One-Time State Migration

If older state still contains `cloudflare_*` resources, Terraform runs can fail while decoding state.
Run this **once per environment** (dev/prod) from that environment directory:

```bash
terraform init -upgrade
terraform state list | grep -E '^cloudflare_' || true
terraform state rm <each cloudflare_* address shown above>
```

`terraform state rm` edits Terraform state only; it does not delete real DNS records.
