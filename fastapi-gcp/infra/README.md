# infra

`app/` の FastAPI を Cloud Run にデプロイし、IAP で Google アカウント認証を必須にする Terraform 構成。

## 構成

- **Artifact Registry** (Docker): コンテナイメージの置き場
- **Cloud Run** (`google_cloud_run_v2_service`, `iap_enabled = true`): IAP ダイレクト統合を有効化
- **IAM**:
  - IAP サービスエージェント → `roles/run.invoker`（IAP だけが Cloud Run を呼べる）
  - `var.iap_members` → `roles/iap.httpsResourceAccessor`（ログインを許可する Google アカウント）
- **ランタイム SA**: Cloud Run 専用のサービスアカウント（`roles/logging.logWriter` のみ）

ロードバランサ + Serverless NEG ではなく IAP ダイレクト統合を採用しているため、
独自ドメイン・SSL 証明書・外部 IP・OAuth ブランドの作成は不要で、LB の固定費もかかりません。
`*.run.app` の URL にそのままアクセスすると IAP のログイン画面が出ます。

## 前提

- `gcloud auth application-default login` 済み
- 対象プロジェクトで課金が有効

## デプロイ手順

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars   # project_id と iap_members を編集
terraform init
```

### 1. API 有効化と Artifact Registry を先に作る

イメージが存在しないと Cloud Run のデプロイが失敗するため、リポジトリを先に作成します。

```bash
terraform apply \
  -target=google_project_service.this \
  -target=google_artifact_registry_repository.app
```

### 2. イメージをビルドして push

```bash
REPO=$(terraform output -raw artifact_registry_repository)

gcloud builds submit ../app --tag "${REPO}/fastapi-gcp:latest"
```

（ローカルの Docker で push する場合）

```bash
gcloud auth configure-docker "$(terraform output -raw artifact_registry_repository | cut -d/ -f1)"
docker build --platform linux/amd64 -t "${REPO}/fastapi-gcp:latest" ../app
docker push "${REPO}/fastapi-gcp:latest"
```

### 3. 残りを apply

```bash
terraform apply
terraform output service_url
```

出力された URL にブラウザでアクセスすると、Google アカウントのログインが要求されます。
`iap_members` に含まれないアカウントは 403 になります。

## 補足

- IAP を有効化した直後は反映まで数分かかることがあります。
- IAP は認証済みユーザー情報を `X-Goog-Authenticated-User-Email` などのヘッダで渡します。
  アプリ側で本人確認をする場合は、ヘッダを信用せず `X-Goog-IAP-JWT-Assertion` の JWT を検証してください。
- イメージを更新したら `image_tag` を変えて `terraform apply` するか、同じタグを push し直して
  `terraform apply -replace=google_cloud_run_v2_service.app` します。
