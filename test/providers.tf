terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

    backend "s3" {
    bucket         = "sampozki-thesis-state"
    key            = "test-terraform.tfstate"
    region         = "eu-north-1"
    encrypt        = false
    use_lockfile   = true
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = var.default_tags
  }
}

