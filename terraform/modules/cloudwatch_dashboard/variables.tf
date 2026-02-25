variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "metrics_namespace" {
  type    = string
  default = "Payme/API"
}
