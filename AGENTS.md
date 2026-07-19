# Repository Rules

## Cloud Run

- project_id: simple-alert-line-bot
- service_name: simple-alert-line-bot
- region: asia-northeast1
- runtime_service_account: simple-alert-line-bot@simple-alert-line-bot.iam.gserviceaccount.com
- デプロイは `cloudbuild.yaml` と Cloud Build トリガー `simple-alert-line-bot-cd` 経由のみ。Console の「Cloud Run にデプロイ」と `gcloud run deploy --source` は使用しない。
- 設定変更や再デプロイで費用が生じ得る場合は、実行前に課金要因・概算・無料枠・増額条件・代替案を説明する。
- GCP を扱う日の最初の作業では、Budget アラート、Cloud Run のスケール設定、Cloud Build トリガー数、Artifact Registry の保存状況を確認して費用監視状況を報告する。

## Test Policy

- Use the repository `venv` for running tests and installing dependencies.
- Use the Firestore Emulator for local integration tests.
