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
  default = "sk_live_placeholder"
}

variable "google_client_id_placeholder" {
  type    = string
  default = "google-client-id-placeholder"
}

variable "google_client_secret_placeholder" {
  type    = string
  default = "google-client-secret-placeholder"
}

variable "cloudflaire_api_token_placeholder" {
  type    = string
  default = "cloudflare-api-token-placeholder"
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
  default = "payme"
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

variable "lambda_source_dir" {
  type    = string
  default = "../../../build/lambda"
}

variable "parameter_prefix" {
  type    = string
  default = "/payme/prod"
}

variable "frontend_build_dir" {
  type    = string
  default = "../../../frontend/dist"
}

variable "frontend_domain_aliases" {
  type    = list(string)
  default = []
}

variable "frontend_acm_certificate_arn" {
  type    = string
  default = ""
}

variable "cloudflare_api_token" {
  type      = string
  sensitive = true
  default   = ""
}

variable "cloudflare_zone_name" {
  type    = string
  default = "quidme.uk"
}

variable "cloudflare_record_name" {
  type    = string
  default = "@"
}

variable "cloudflare_proxied" {
  type    = bool
  default = true
}
