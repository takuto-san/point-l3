locals {
  name = "${var.project_name}-${var.environment}"
}

resource "aws_iam_role" "l3_export" {
  name = "${local.name}-export"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "l3_export" {
  name = "publish-approved-results"
  role = aws_iam_role.l3_export.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "PublishToManagementEventBus"
      Effect   = "Allow"
      Action   = ["events:PutEvents"]
      Resource = var.management_event_bus_arn
    }]
  })
}
