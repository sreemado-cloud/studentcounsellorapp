terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.30"
    }
    http = {
      source  = "hashicorp/http"
      version = ">= 3.4"
    }
    tls = {
      source  = "hashicorp/tls"
      version = ">= 4.0"
    }
  }

  # Uncomment and configure for remote state (recommended for production)
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "student-counsellor/eks/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "student-counsellor"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
