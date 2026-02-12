terraform {
  backend "s3" {
    bucket         = "payme-terraform-state-dev"
    key            = "payme/dev/terraform.tfstate"
    region         = "eu-west-2"
    dynamodb_table = "payme-terraform-lock-dev"
    encrypt        = true
  }
}
