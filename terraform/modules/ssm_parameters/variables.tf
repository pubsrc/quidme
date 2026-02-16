variable "service_fee_bps_name" { type = string }
variable "service_fee_bps_value" { type = number }

variable "service_fee_fixed_name" { type = string }
variable "service_fee_fixed_value" { type = number }

variable "payme_base_url_name" { type = string }
variable "payme_base_url_value" { type = string }

variable "account_refresh_url_name" { type = string }
variable "account_refresh_url_value" { type = string }

variable "account_return_url_name" { type = string }
variable "account_return_url_value" { type = string }

variable "cognito_domain_prefix_name" { type = string }
variable "cognito_domain_prefix_value" { type = string }

variable "callback_urls_name" { type = string }
variable "callback_urls_value" { type = list(string) }

variable "logout_urls_name" { type = string }
variable "logout_urls_value" { type = list(string) }

variable "expiry_schedule_name" { type = string }
variable "expiry_schedule_value" { type = string }

variable "cors_allowed_origins_name" { type = string }
variable "cors_allowed_origins_value" { type = list(string) }

variable "vite_api_base_url_name" { type = string }
variable "vite_api_base_url_value" { type = string }

variable "vite_cognito_user_pool_id_name" { type = string }
variable "vite_cognito_user_pool_id_value" { type = string }

variable "vite_cognito_user_pool_client_id_name" { type = string }
variable "vite_cognito_user_pool_client_id_value" { type = string }

variable "vite_cognito_region_name" { type = string }
variable "vite_cognito_region_value" { type = string }

variable "vite_cognito_oauth_domain_name" { type = string }
variable "vite_cognito_oauth_domain_value" { type = string }

variable "vite_oauth_redirect_sign_in_name" { type = string }
variable "vite_oauth_redirect_sign_in_value" { type = string }

variable "vite_oauth_redirect_sign_out_name" { type = string }
variable "vite_oauth_redirect_sign_out_value" { type = string }

variable "tags" {
  type    = map(string)
  default = {}
}
