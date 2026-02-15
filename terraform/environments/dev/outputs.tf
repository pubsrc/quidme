output "api_endpoint" {
  value = module.api_gateway.api_endpoint
}

output "api_base_url" {
  value = trimspace(var.api_domain_name) == "" ? module.api_gateway.api_endpoint : "https://${var.api_domain_name}"
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

output "frontend_cloudfront_distribution_id" {
  value = module.frontend_hosting.cloudfront_distribution_id
}

output "frontend_url" {
  value = module.frontend_hosting.frontend_url
}

output "frontend_domain_aliases" {
  value = module.frontend_hosting.domain_aliases
}

output "stripe_webhook_secret_name" {
  value = module.secrets.stripe_webhook_secret_name
}
