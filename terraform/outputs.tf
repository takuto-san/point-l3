output "l3_account_id" {
  value = var.l3_account_id
}

output "l3_export_role_arn" {
  value = aws_iam_role.l3_export.arn
}
