variable "project_name" {
  type = string
}

variable "lambda_invoke_arn" {
  type = string
}

variable "lambda_function_name" {
  type = string
}

variable "cognito_user_pool_id" {
  type = string
}

variable "cognito_app_client_id" {
  type = string
}

variable "region" {
  type = string
}

variable "cors_allowed_origins" {
  description = "Allowed CORS origins for the HTTP API. Keep this as explicit origins in production."
  type        = list(string)
  default     = ["*"]
}

variable "tags" {
  type    = map(string)
  default = {}
}
