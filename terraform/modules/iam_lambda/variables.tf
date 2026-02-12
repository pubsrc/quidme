variable "project_name" {
  type = string
}

variable "dynamodb_table_arns" {
  type = list(string)
}

variable "dynamodb_index_arns" {
  type    = list(string)
  default = []
}

variable "tags" {
  type    = map(string)
  default = {}
}
