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
  value = module.cognito.domain
  sensitive = true
}
