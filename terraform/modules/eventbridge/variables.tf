variable "rule_name" {
  type = string
}

variable "schedule_expression" {
  type = string
}

variable "lambda_arn" {
  type = string
}

variable "lambda_function_name" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
