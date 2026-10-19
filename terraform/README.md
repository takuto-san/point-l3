# Terraform

## 構成図

![L3アカウントと管理アカウントを分離したAWS構成図](../diagrams/aws-architecture.png)

L3側のECR＋Lambdaコンテナ、Step Functions Standard、単一AZ・単一プライベートサブネット構成は目標構成であり、現時点のTerraformには未実装です。Step Functions自体はVPC外のAWSマネージドサービスで、図中のworkflow枠は制御状態を省略して4つのLambdaだけを示した論理的なオーケストレーション範囲です。

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
