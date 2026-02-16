# Cloudflare Registrar / Route 53 DNS (Prod)

Prod DNS is managed in Route 53. Cloudflare is treated as the registrar only.

## Why

- Avoid Cloudflare provider state/schema drift.
- Keep DNS + ACM validation fully automated in AWS.

## What Terraform Manages Now

- **AWS resources** (API Gateway, Lambda, Cognito, DynamoDB, CloudFront, S3, ACM).
- **Route 53 hosted zone + records (prod only)**: apex + www -> CloudFront, api -> API Gateway, and ACM DNS validation.

## Cloudflare Setup (One-Time)

After a successful `terraform apply` in `terraform/environments/prod`, update your domain's
nameservers at Cloudflare (registrar) to the Route 53 values:

```bash
cd terraform/environments/prod
terraform output -raw route53_zone_name_servers
```

DNS propagation depends on the registrar and can take time.

## One-Time State Migration

If older state still contains `cloudflare_*` resources, Terraform runs can fail while decoding state.
Run this **once per environment** (dev/prod) from that environment directory:

```bash
terraform init -upgrade
terraform state list | grep -E '^cloudflare_' || true
terraform state rm <each cloudflare_* address shown above>
```

`terraform state rm` edits Terraform state only; it does not delete real DNS records.
