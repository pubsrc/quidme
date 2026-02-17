# Cloudflare DNS (Prod)

Prod DNS is managed in Cloudflare. Terraform creates and updates Cloudflare DNS records directly.

## What Terraform Manages

- **AWS resources** (API Gateway, Lambda, Cognito, DynamoDB, CloudFront, S3, ACM).
- **Cloudflare DNS records (prod only)**:
  - `@` and wildcard frontend aliases -> CloudFront
  - `api` -> API Gateway custom domain target
  - ACM DNS validation records for API and frontend certificates (when Terraform manages cert issuance)

## Required CI/CD Secret

Set Cloudflare token in your deployment environment:

- `TF_VAR_cloudflare_api_token`

Token scope should be limited to:

- Zone: Read
- DNS: Edit

## Required Prod Variable

In `terraform/environments/prod/terraform.tfvars`:

```hcl
cloudflare_zone_name = "quidme.uk"
```

## Cloudflare Dashboard Settings

- Keep `quidme.uk`, `www.quidme.uk`, `api.quidme.uk` as **DNS only** (not proxied) unless you intentionally want Cloudflare proxy in front of CloudFront/API Gateway.
- Keep nameservers managed in Cloudflare for this setup.
