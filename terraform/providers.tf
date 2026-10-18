provider "aws" {
  region              = var.aws_region
  profile             = var.l3_aws_profile
  allowed_account_ids = [var.l3_account_id]

  default_tags {
    tags = merge({
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      DataClass   = "Restricted"
    }, var.tags)
  }
}
