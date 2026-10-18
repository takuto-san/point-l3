# point-l3

解約金還元申請システムのL3アカウント側の定義。管理システムは別リポジトリ `takuto-san/point` で管理する。

## 配置と責務

- `terraform/`：持出許可済みの審査結果を管理側EventBridgeへ送るIAMロール。
- `openapi/l3-management.openapi.yaml`：管理側が提供するPUT/GETと、共通のAnalysisSnapshotの契約コピー。
- `docker-compose.yml`：送信先のAPI契約を閲覧するSwagger UI。

現在のコードにはL3が提供するWebhook/API、OCR、マスク・持出審査、送信Lambda本体は含まれていない。今回の移設では既存のL3用Terraformと連携契約を配置し、新しい業務APIは追加していない。

通常経路は `L3の送信処理 → 管理アカウントのEventBridge → SQS → 受信Lambda → DynamoDB`。本リポジトリのロールは `events:PutEvents` のみを許可する。OpenAPIのHTTPS経路は管理アカウント内の照会・検証用で、L3からのクロスアカウントHTTPS呼び出し権限は含まない。

## Terraform

管理側のTerraformを先に用意し、出力 `management_event_bus_arn` を取得する。

```bash
# pointリポジトリ側
terraform -chdir=../point/terraform output -raw management_event_bus_arn
```

`terraform/terraform.tfvars.example` を `terraform/terraform.tfvars` にコピーし、L3のプロファイル・アカウントID・管理側EventBridge ARNを設定する。

```bash
terraform -chdir=terraform init
terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
terraform -chdir=terraform plan -var-file=terraform.tfvars
```

管理側の `l3_account_id` と本リポジトリの `l3_account_id` を一致させる。リージョンも送信先EventBridgeと揃える。stateは各リポジトリで独立して管理し、隣接チェックアウトやremote stateへの直接参照は不要。

既存の送信Lambdaに出力 `l3_export_role_arn` を実行ロールとして設定する場合、Lambda自身に必要なログ・L3データへの権限は、そのLambdaの構成側で追加する。このロール単独では送信Lambdaをデプロイしない。

## API契約の閲覧

```bash
docker compose up --build -d
# http://localhost:8081
```

OpenAPIの正本は `point/openapi/l3-management.openapi.yaml`（管理側受信API）で、本リポジトリにはv0.2.0をコピーしている。契約更新時は両リポジトリを同時に更新し、同一内容に保つ。独立して内容を書き換えない。

隣接してチェックアウトした開発環境での更新例：

```bash
cp ../point/openapi/l3-management.openapi.yaml openapi/l3-management.openapi.yaml
```

## 移設範囲

`point/terraform/l3.tf` のIAMロール・ポリシーを移設した。リソース名は維持し、管理EventBridgeへの直接参照を入力変数へ置き換えている。AWSへの適用やstate移動は実行していない。既存環境で適用済みの場合は、元stateからL3用stateへリソースを移管してから両方のplanを確認すること。
