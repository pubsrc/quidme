output "api_endpoint" {
  value = module.api_gateway.api_endpoint
}

output "cognito_user_pool_id" {
  value = module.cognito.user_pool_id
}

output "cognito_user_pool_client_id" {
  value = module.cognito.app_client_id
}

output "cognito_domain" {
  value     = module.cognito.domain
  sensitive = true
}

output "frontend_bucket_name" {
  value = module.frontend_hosting.bucket_name
}

output "frontend_cloudfront_domain_name" {
  value = module.frontend_hosting.cloudfront_domain_name
}

output "frontend_url" {
  value = module.frontend_hosting.frontend_url
}

output "frontend_domain_aliases" {
  value = module.frontend_hosting.domain_aliases
}

output "cloudflaire_api_token_secret_name" {
  value = module.secrets.cloudflaire_api_token_secret_name
}

output "cloudflare_frontend_record_id" {
  value = cloudflare_record.frontend_dev.id
}
