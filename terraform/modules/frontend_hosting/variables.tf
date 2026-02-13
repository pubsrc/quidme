variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "frontend_build_dir" {
  type = string
}

variable "domain_aliases" {
  type    = list(string)
  default = []
}

variable "acm_certificate_arn" {
  type    = string
  default = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
