variable "user_pool_name" {
  type = string
}

variable "app_client_name" {
  type = string
}

variable "domain_prefix" {
  type = string
}

variable "google_client_id" {
  type = string
}

variable "google_client_secret" {
  type      = string
  sensitive = true
}

variable "callback_urls" {
  type = list(string)
}

variable "logout_urls" {
  type = list(string)
}

variable "tags" {
  type    = map(string)
  default = {}
}
