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

variable "stripe_connected_webhook_secret_name" {
  type = string
}

variable "stripe_connected_webhook_secret_placeholder" {
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

variable "tags" {
  type    = map(string)
  default = {}
}

variable "recovery_window_in_days" {
  description = "Secrets Manager recovery window. Set to 0 to allow immediate recreation after destroy."
  type        = number
  default     = 0
}
