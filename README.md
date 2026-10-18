# L3環境 — point-l3

他社解約金還元申請の証跡・個人情報をL3内で扱い、本人確認とポイント付与判定を支援する側のリポジトリ。管理システムは [point](https://github.com/takuto-san/point) で管理する。

設計の基準は「管理システム」チャットの最新の全体像・画面仕様。証跡精査の工数を月約30時間削減し、7日以内に審査結果を通知することを業務目標とする。現時点でこのリポジトリにあるAWSリソース定義は、管理側へ結果を送るIAMロール・ポリシーのみ。

## 環境セットアップ

### 必要なツール

| ツール | 用途 |
|---|---|
| Git | ソースの取得 |
| Docker / Docker Compose v2 | Swagger UIの起動。Docker Desktop等を起動しておく |
| Terraform 1.6以上 | L3用AWS構成の初期化・検証・構築 |
| AWS CLI v2 | AWSへ構築する場合の認証・アカウント確認 |

Swagger UIの閲覧にAWSアカウント・認証情報は不要。このリポジトリには実行アプリやNode.jsテストがないため、Node.jsの導入・`npm install` も不要。

### 1. リポジトリを取得する

```bash
git clone https://github.com/takuto-san/point-l3.git
cd point-l3
```

以下のコマンドは、特記がない限りリポジトリのルートで実行する。

### 2. Swagger UIを起動する

```bash
docker compose up --build -d --wait
docker compose ps
```

[http://localhost:8081](http://localhost:8081) を開く。これは管理側のAPI契約を閲覧するUIで、L3のWebhook/API本体のローカル起動ではない。停止する場合は `docker compose down` を実行する。ポートが重複する場合は `SWAGGER_PORT=18081 docker compose up --build -d --wait` で変更できる。

### 3. Terraformを設定・検証する

初回のみ設定例をコピーし、`terraform/terraform.tfvars` を編集する。既存の設定ファイルがある場合はコピーを省略する。

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
terraform -chdir=terraform init
terraform -chdir=terraform fmt -check
terraform -chdir=terraform validate
```

| 設定項目 | 設定する値 |
|---|---|
| `l3_aws_profile` | L3アカウント用AWSプロファイル名。例：`l3-dev` |
| `l3_account_id` | 適用先L3アカウントの12桁ID。point側の同名変数と一致させる |
| `management_event_bus_arn` | pointのTerraform出力から取得する管理側イベントバスARN |
| `aws_region` | 管理側EventBridgeと同じリージョン。初期値：`ap-northeast-1` |

設定例のアカウントID・イベントバスARNは仮の値なので、構築前に実環境の値へ置き換える。`init` はプロバイダ取得のためネット接続が必要だが、`validate` までの手順にAWS認証情報は不要。`terraform.tfvars` とstateはGit管理対象外。

### 4. AWSへ接続・構築する場合

構築順序は **point（管理側）→ point-l3（L3側）**。先に [pointの環境セットアップ](https://github.com/takuto-san/point#環境セットアップ) に従って管理側を構築し、イベントバスARNを取得する。隣接してチェックアウトしている場合は、以下で確認できる。

```bash
terraform -chdir=../point/terraform output -raw management_event_bus_arn
```

取得した値を `terraform/terraform.tfvars` の `management_event_bus_arn` へ設定する。隣接チェックアウトがない場合は、管理側の担当者からARNを受け取って設定してもよい。

組織の認証手順に従ってL3アカウント用プロファイルを用意し、`l3_aws_profile` と同じ名前で認証する。例の `l3-dev` は実際の名前に置き換える。

```bash
aws sts get-caller-identity --profile l3-dev
terraform -chdir=terraform plan -var-file=terraform.tfvars
```

表示されたアカウントIDと `l3_account_id` が一致することを確認する。AWSリソースを構築する場合は、planの内容を確認してから実行する。

```bash
terraform -chdir=terraform apply -var-file=terraform.tfvars
terraform -chdir=terraform output -raw l3_export_role_arn
```

出力は将来の送信Lambdaへ割り当てる実行ロールのARN。現在はIAMロール・ポリシーの構築までで、Webhook・OCR・送信Lambda本体は起動しない。

## システム概要

「管理システム」チャットでCodexのdiagram-designを使って作成した、全体構成と画面仕様の図。両リポジトリで同じ図を掲載し、L3側と管理側の役割を共有する。L3の受付・解析・持出審査・送信コードは未実装。

![解約金還元申請システムの全体構成と画面仕様](docs/point-award-system-overview-with-screens.png)

[SVG版](docs/point-award-system-overview-with-screens.svg) ／ [編集用HTML](docs/point-award-system-overview-with-screens.html)

既存図を内容変更せず掲載している。図中のTextractは当初の検討案で、現在のOCR/AIサービスは未選定。図の矢印・破線は元の凡例に従い、実装済み／未実装の区分は下の表を参照。

L3側の処理方針：

1. formrunのWebhookを起点に申請・証跡を取り込み、L3内で保持する。Webhookの実際のペイロードと証跡取得方式は未確定。
2. OCR等で氏名・解約金総額を抽出し、本人確認とポイント付与判定を別々に実行する。OCR/AIサービスは未選定。
3. 本人確認は回線契約者の氏名と照合し、ポイント付与判定は営業・運用部門で確認済みのルールを参照する。AIの判定出力は「結果・理由」のみ。
4. 完了した結果を持出審査・マスク処理に通し、版付きスナップショットで管理側へ順次送る。
5. 担当者による「結果・理由」の修正と「確定」、メールリストの連携、配信完了後のマイページ結果更新は管理側が担当する。

原本・未マスクの個人情報・OCR全文・メールアドレスは管理系へ渡さない。マスク済み比較情報やNIFTY IDも、持出許可がある項目だけを送る。担当者が原本を確認する導線は「formrunで開く」とする。

| 業務イベント | マイページの表示 |
|---|---|
| formrunで申請受付 | 受付済み |
| 申請管理システムへの取込 | 審査中 |
| メール配信完了を連携 | 結果 |

マイページは既存の独立した表示先とし、メール送信可能になった時点ではなく、配信完了後に結果を公開する。ポイント実付与はこの全体像に含めない。

## AWS構成図

L3側TerraformのplanからTerravisionで生成した構成図。現在の定義は送信用IAMロールとインラインポリシーの2リソースのみ。IAMリソースを表示するため、簡略化オプションは使わずに生成する。

![Terravisionで生成したL3アカウントのAWS構成図](docs/architecture-aws.dot.png)

[SVG版](docs/architecture-aws.dot.svg)

図は仮のアカウントIDによる設計図。送信先EventBridgeはpoint側の定義なので、L3側の作成対象には含まれない。ロールの信頼先は `lambda.amazonaws.com`、許可する送信先は `management_event_bus_arn` のイベントバスのみ。

API Gateway、証跡用S3・DB、OCR/AI、送信Lambda、VPC・サブネット・NATは現在のTerraformに含まれていない。業務処理の全体像は上のシステム概要を参照。

## ディレクトリ構成

```text
point-l3/
├── README.md
├── Dockerfile                         # API契約閲覧用のSwagger UI
├── docker-compose.yml                 # localhost:8081
├── .dockerignore
├── .gitignore                         # state・ローカル設定等を除外
├── openapi/
│   └── l3-management.openapi.yaml      # 管理側受信APIの契約コピー
├── terraform/
│   ├── versions.tf                    # Terraform・AWSプロバイダのバージョン
│   ├── providers.tf                   # L3アカウントへの接続
│   ├── variables.tf                   # アカウントID・送信先ARN等
│   ├── l3.tf                          # 送信用IAMロール・ポリシー
│   ├── outputs.tf                     # l3_account_id・l3_export_role_arn
│   ├── terraform.tfvars.example        # 設定例
│   └── .terraform.lock.hcl             # AWSプロバイダの固定
├── tools/
│   ├── diagram.sh                     # Terravision構成図の再生成
│   └── diagram-providers.tf.txt        # 図生成専用の仮プロバイダ設定
└── docs/
    ├── architecture-aws.dot.png
    ├── architecture-aws.dot.svg
    ├── point-award-system-overview-with-screens.png
    ├── point-award-system-overview-with-screens.svg
    └── point-award-system-overview-with-screens.html
```

生成物・ローカル設定の `.terraform/`、state、`terraform.tfvars` はGit管理対象外。管理側の受信API本体・Lambda・DBはpointに置き、AWS構成図の生成ツールは各リポジトリに置く。

## 実装状況とリポジトリの分担

| 項目 | 担当 | 現在の状態 |
|---|---|---|
| 結果送信用IAMロール・EventBridge送信権限 | point-l3 | Terraform定義あり |
| 管理側API・共通AnalysisSnapshotの契約 | pointが正本、point-l3がコピー | OpenAPIあり |
| formrun Webhook受付・証跡取得・保存 | point-l3 | 未実装 |
| OCR・本人確認・ポイント付与判定 | point-l3 | 未実装。サービス・業務ルールの確定が必要 |
| マスク・持出審査・版採番・結果送信 | point-l3 | 未実装 |
| EventBridge・SQS・受信Lambda・DynamoDB | point | 定義・受信コードあり |
| 管理画面、修正・確定API、メール・マイページ連携 | point | 未実装 |

## 管理側との接続

point側の `l3_account_id` と本リポジトリの `l3_account_id`、送信先のリージョンを揃える。AWSプロバイダは `allowed_account_ids` でL3への適用を検証する。stateは両リポジトリで独立し、互いのstateや隣接チェックアウトへの実行時依存はない。

出力 `l3_export_role_arn` を送信Lambdaの実行ロールに設定する際は、ログ・L3データ等の必要な権限を送信Lambdaの実装側で追加する。

## API契約の同期

起動手順は上部の「環境セットアップ」を参照。契約の正本は [pointのOpenAPI](https://github.com/takuto-san/point/blob/main/openapi/l3-management.openapi.yaml) で、[このリポジトリのコピー](openapi/l3-management.openapi.yaml) はv0.2.0。契約更新時は両リポジトリを同じ内容に保つ。

```bash
# 隣接チェックアウトでの契約更新例
cp ../point/openapi/l3-management.openapi.yaml openapi/l3-management.openapi.yaml
```

通常の結果送信はEventBridgeを使用する。イベントの `source` は `jp.co.nifty.point-award.l3`、`detail-type` は `AnalysisSnapshot.v1`、`detail` はOpenAPIの `AnalysisSnapshot` とする。`applicationId` と単調増加する `revision` で再送・順序逆転に対応し、各版には差分ではなく全状態を含める。

OpenAPIのPUT/GETは管理側が提供するIAM認可の受信・受信票API。現在のTerraformはL3からの直接クロスアカウントHTTPS呼び出し権限を付与しない。

## 移設済み環境について

元の `point/terraform/l3.tf` のIAMロール・ポリシーを移設し、リソース名を維持した。送信先は管理側リソースの直接参照から入力変数へ変更している。既存環境で旧構成を適用済みの場合は、L3リソースのstateをこのリポジトリへ移管してから両方のplanを確認する。

## AWS構成図の再生成

```bash
bash tools/diagram.sh
```

TerraformとDockerが必要。図生成専用の一時コピー・仮の認証情報でplanを作り、固定digestのTerravision公式DockerイメージでPNG/SVGを生成する。AWS API・実stateは参照せず、AWSへの適用も行わない。
