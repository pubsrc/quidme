terraform {
  backend "s3" {
    bucket         = "payme-terraform-state-prod"
    key            = "payme/prod/terraform.tfstate"
    region         = "eu-west-2"
    dynamodb_table = "payme-terraform-lock-prod"
    encrypt        = true
  }
}
