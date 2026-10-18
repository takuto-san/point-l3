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

## 3. ディレクトリ構成

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

## 4. AWS構成図

![AWS構成図](diagrams/aws-architecture.png)

この図は目標構成です。L3側は単一AZ・単一プライベートサブネットに処理Lambdaを集約します。VPC・AZ・サブネットとLambdaのVPC接続は現時点のTerraformには未実装です。
