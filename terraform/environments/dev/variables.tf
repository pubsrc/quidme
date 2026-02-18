variable "project_name" {
  type    = string
  default = "payme"
}

variable "aws_region" {
  type    = string
  default = "eu-west-2"
}

variable "stripe_secret_placeholder" {
  type    = string
  default = "sk_test_placeholder"
}

variable "stripe_webhook_secret_placeholder" {
  type    = string
  default = "stripe-webhook-secret-placeholder"
}

variable "google_client_id_placeholder" {
  type    = string
  default = "google-client-id-placeholder"
}

variable "google_client_secret_placeholder" {
  type    = string
  default = "google-client-secret-placeholder"
}

variable "service_fee_bps_default" {
  type    = number
  default = 500
}

variable "service_fee_fixed_default" {
  type    = number
  default = 50
}

variable "payme_base_url_default" {
  type    = string
  default = "https://example.com"
}

variable "account_refresh_url_default" {
  type    = string
  default = "https://example.com/refresh"
}

variable "account_return_url_default" {
  type    = string
  default = "https://example.com/return"
}

variable "cognito_domain_prefix_default" {
  type    = string
  default = "payme-dev"
}

variable "callback_urls_default" {
  type    = list(string)
  default = []
}

variable "logout_urls_default" {
  type    = list(string)
  default = []
}

variable "expiry_schedule_default" {
  type    = string
  default = "rate(15 minutes)"
}

variable "cors_allowed_origins_default" {
  type    = list(string)
  default = ["*"]
}

variable "vite_cognito_user_pool_id_default" {
  description = "Deprecated. Frontend Cognito values are now derived from Terraform resources."
  type        = string
  default     = "eu-west-2_placeholder"
}

variable "vite_cognito_user_pool_client_id_default" {
  description = "Deprecated. Frontend Cognito values are now derived from Terraform resources."
  type        = string
  default     = "placeholder"
}

variable "lambda_source_dir" {
  type    = string
  default = "../../../build/lambda"
}

variable "parameter_prefix" {
  description = "Deprecated. SSM parameter sync is no longer used for runtime/frontend config."
  type        = string
  default     = "/payme/dev"
}

variable "frontend_domain_aliases" {
  description = "Deprecated: frontend aliases are managed in constants.tf."
  type        = list(string)
  default     = []
}

variable "frontend_acm_certificate_arn" {
  type    = string
  default = ""
}

variable "api_domain_name" {
  type    = string
  default = ""
}

variable "api_acm_certificate_arn" {
  type    = string
  default = ""
}
