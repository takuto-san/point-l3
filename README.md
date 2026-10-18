# L3環境

## 概要

他社解約金還元申請の顧客情報と証跡をL3アカウント内に保持し、証跡解析・本人確認・ポイント付与判定を行う。管理システムには、持出制御を通過した結果だけを連携する。

![解約金還元申請システムの全体像](diagrams/system-overview.png)

## 1. 依存関係

| 名前 | バージョン |
|---|---|
| Docker / Docker Compose | Compose v2 |
| Terraform | 1.6.0以上 |
| AWS CLI | v2 |
| Swagger UI | 5.33.1 |
| Diagram-as-Code (`awsdac`) | v0.23 |

## 2. セットアップ

```bash
git clone https://github.com/takuto-san/point-l3.git
cd point-l3
docker compose up --build -d --wait
docker compose ps
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
terraform -chdir=terraform init
terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
awsdac aws-architecture.yml --output diagrams/aws-architecture.png --force
```

Swagger UI は <http://localhost:8081> で確認できる。ポートを変更する場合は、例えば
`SWAGGER_PORT=18081 docker compose up --build -d --wait` とする。終了時は
`docker compose down` を実行する。起動中に `openapi.yml` を編集した場合は、イメージの
再ビルドをせずブラウザの再読み込みだけで変更を確認できる。

### Docker構成の選定

- OpenAPI定義の閲覧用途に限定し、独自のWebサーバーは実装せず公式Swagger UIイメージを使用する。
- 再現性のため`latest`を避け、OpenAPI 3.1対応のSwagger UI 5.33.1へ固定する。
- 定義ファイルをイメージへ含め、同じイメージをローカル確認と配布の両方に使用できるようにする。
- ローカルでは定義ファイルを読み取り専用でマウントし、編集内容を即時反映する。
- 公開先をループバックアドレスに限定し、コンテナ内の権限昇格を抑止する。
- このイメージはAPIドキュメント表示専用であり、L3処理の実行環境ではない。

## 3. L3処理基盤仕様

L3の処理基盤は、Amazon ECRに格納したコンテナイメージをAWS Lambdaで実行する。ECSおよびFargateは使用しない。

- `申請・証跡取込`、`本人確認`、`付与判定`、`持出制御`を独立したLambdaとして構成する。
- LambdaはZIPではなくコンテナイメージ形式とし、同一リージョンのECRからデプロイする。
- ECRリポジトリはLambda単位で分離し、タグの上書きを禁止してイメージスキャンを有効にする。
- 4つのLambdaはL3処理VPC内の単一AZ・単一プライベートサブネットへ配置する。
- 状態遷移にはStep Functions Standard Workflowを使用し、各Lambdaの順序、リトライ、タイムアウト、異常終了を定義する。
- 証跡本体と大きな解析結果はS3に保持し、Step Functionsでは`applicationId`、`revision`、S3のbucket/keyなどの参照情報だけを受け渡す。
- 各Lambdaは`applicationId`と`revision`を冪等性キーとして、再試行時の二重処理を防止する。

基本状態遷移は次のとおり。

```text
Webhook受付
  → Step Functions Standardを開始
  → 申請・証跡取込（証跡をS3へ保存）
  → 本人確認（Textractによる証跡抽出、Bedrockによる判定支援）
  → 付与判定
  → 持出制御
  → 管理側EventBridgeへ結果送信
  → 正常終了
```

各Taskの一時的な失敗は上限付きで再試行し、回復不能なエラーは`Catch`で失敗状態へ遷移させる。管理側へ送信できるのは、持出制御を正常に通過した結果だけとする。

構成図のStep Functions枠線はオーケストレーション範囲を表し、ネットワーク境界ではない。Lambdaはプライベートサブネットへ接続するが、Step Functions自体はVPC外のAWSマネージドサービスとして動作する。

## 4. ディレクトリ構成

```text
point-l3/
├── README.md
├── aws-architecture.yml
├── openapi.yml
├── Dockerfile
├── docker-compose.yml
├── terraform/
│   ├── README.md
│   ├── *.tf
│   └── terraform.tfvars.example
└── diagrams/
    ├── aws-architecture.png
    └── system-overview.png
```

## 5. AWS構成図

![AWS構成図](diagrams/aws-architecture.png)

この図は目標構成です。L3側はECRのコンテナイメージを使用する4つのLambdaを単一AZ・単一プライベートサブネットに配置し、Step Functions Standardで状態遷移を管理します。ECR、Step Functions、VPC、サブネットとLambdaの接続は現時点のTerraformには未実装です。
