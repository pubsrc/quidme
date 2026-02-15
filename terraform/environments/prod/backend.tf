terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.0"
    }
  }

  backend "s3" {
    bucket         = "payme-terraform-state-prod"
    key            = "payme/prod/terraform.tfstate"
    region         = "eu-west-2"
    dynamodb_table = "payme-terraform-lock-prod"
    encrypt        = true
  }
}
