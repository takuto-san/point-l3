variable "project_name" {
  type    = string
  default = "point-award"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "aws_region" {
  description = "L3と管理側EventBridgeのリージョン。"
  type        = string
  default     = "ap-northeast-1"
}

variable "l3_aws_profile" {
  description = "L3アカウントのAWS CLIプロファイル。"
  type        = string
}

variable "l3_account_id" {
  description = "適用先L3アカウントID。"
  type        = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.l3_account_id))
    error_message = "12桁のAWSアカウントIDを指定してください。"
  }
}

variable "management_event_bus_arn" {
  description = "pointのTerraform出力management_event_bus_arn。"
  type        = string
  validation {
    condition     = can(regex("^arn:aws[a-z-]*:events:[a-z0-9-]+:[0-9]{12}:event-bus/.+$", var.management_event_bus_arn))
    error_message = "管理側EventBridgeイベントバスのARNを指定してください。"
  }
}

variable "tags" {
  type    = map(string)
  default = {}
}
