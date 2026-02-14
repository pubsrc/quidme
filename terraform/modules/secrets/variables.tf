variable "stripe_secret_name" {
  type = string
}

variable "stripe_secret_placeholder" {
  type = string
}

variable "stripe_webhook_secret_name" {
  type = string
}

variable "stripe_webhook_secret_placeholder" {
  type = string
}

variable "google_oauth_secret_name" {
  type = string
}

variable "google_client_id_placeholder" {
  type = string
}

variable "google_client_secret_placeholder" {
  type = string
}

variable "cloudflaire_api_token_secret_name" {
  type = string
}

variable "cloudflaire_api_token_placeholder" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
