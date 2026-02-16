output "service_fee_bps_name" {
  value = aws_ssm_parameter.service_fee_bps.name
}

output "service_fee_fixed_name" {
  value = aws_ssm_parameter.service_fee_fixed.name
}

output "payme_base_url_name" {
  value = aws_ssm_parameter.payme_base_url.name
}

output "account_refresh_url_name" {
  value = aws_ssm_parameter.account_refresh_url.name
}

output "account_return_url_name" {
  value = aws_ssm_parameter.account_return_url.name
}

output "cognito_domain_prefix_name" {
  value = aws_ssm_parameter.cognito_domain_prefix.name
}

output "callback_urls_name" {
  value = aws_ssm_parameter.callback_urls.name
}

output "logout_urls_name" {
  value = aws_ssm_parameter.logout_urls.name
}

output "expiry_schedule_name" {
  value = aws_ssm_parameter.expiry_schedule.name
}

output "cors_allowed_origins_name" {
  value = aws_ssm_parameter.cors_allowed_origins.name
}

output "vite_api_base_url_name" {
  value = aws_ssm_parameter.vite_api_base_url.name
}

output "vite_cognito_user_pool_id_name" {
  value = aws_ssm_parameter.vite_cognito_user_pool_id.name
}

output "vite_cognito_user_pool_client_id_name" {
  value = aws_ssm_parameter.vite_cognito_user_pool_client_id.name
}

output "vite_cognito_region_name" {
  value = aws_ssm_parameter.vite_cognito_region.name
}

output "vite_cognito_oauth_domain_name" {
  value = aws_ssm_parameter.vite_cognito_oauth_domain.name
}

output "vite_oauth_redirect_sign_in_name" {
  value = aws_ssm_parameter.vite_oauth_redirect_sign_in.name
}

output "vite_oauth_redirect_sign_out_name" {
  value = aws_ssm_parameter.vite_oauth_redirect_sign_out.name
}
