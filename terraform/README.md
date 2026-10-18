# Terraform

## 構成図

![L3アカウントと管理アカウントを分離したAWS構成図](../diagrams/aws-architecture.png)

L3側の単一AZ・単一プライベートサブネット構成、およびVPC・AZ・サブネットとLambdaのVPC接続は目標構成であり、現時点のTerraformには未実装です。

## ディレクトリ構成

```text
terraform/
├── README.md
├── main.tf
├── variables.tf
├── outputs.tf
├── providers.tf
├── versions.tf
├── terraform.tfvars.example
└── .terraform.lock.hcl
```
