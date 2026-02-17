# Cloudflare DNS (Prod)

Prod DNS is managed manually in Cloudflare. Terraform does not create or update DNS records.

## What Terraform Manages

- **AWS resources** (API Gateway, Lambda, Cognito, DynamoDB, CloudFront, S3, ACM).
- **ACM validation record outputs** to help you create DNS records manually in Cloudflare.

## Manual Cloudflare Records

Create and keep these DNS records in Cloudflare:

- `quidme.uk` / `www.quidme.uk` / `*.quidme.uk` -> CloudFront distribution domain
- `api.quidme.uk` -> API Gateway custom domain target

For certificate issuance (if Terraform-managed certs are used), create ACM validation CNAME records using:

- `terraform output frontend_acm_validation_records`
- `terraform output api_acm_validation_records`

## Cloudflare Dashboard Settings

- Keep `quidme.uk`, `www.quidme.uk`, `api.quidme.uk` as **DNS only** (not proxied) unless you intentionally want Cloudflare proxy in front of CloudFront/API Gateway.
- Keep nameservers managed in Cloudflare for this setup.
