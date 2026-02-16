output "api_endpoint" {
  value = "https://${var.api_domain_name}"
}

output "api_base_url" {
  value = "https://${var.api_domain_name}"
}

output "api_custom_domain_target" {
  value       = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].target_domain_name
  description = "Target domain name for the API custom domain (use for DNS CNAME)."
}

output "api_acm_validation_records" {
  description = "ACM DNS validation records for the API custom domain (create these in your DNS provider)."
  value = local.api_manage_certificate ? [
    for dvo in aws_acm_certificate.api[0].domain_validation_options : {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  ] : []
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

output "frontend_acm_validation_records" {
  description = "ACM DNS validation records for the frontend custom domains (create these in your DNS provider)."
  value = local.frontend_manage_certificate ? [
    for dvo in aws_acm_certificate.frontend[0].domain_validation_options : {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  ] : []
}

output "stripe_webhook_secret_name" {
  value = module.secrets.stripe_webhook_secret_name
}
