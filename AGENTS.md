<!-- Shared guidance from fezzlk/agent-kit @ 1089cb3036e50c7d354c63dbc3c7236321feb6f7. Project-specific guidance follows. -->

# Shared AI development guidance

- Keep changes small, preserve existing user work, and run appropriate verification.
- Do not expose secrets or commit environment values.
- Before cloud or paid API changes, state the likely cost and impact.
- pico is the long-term memory: read its project context and decisions when needed; record completed facts and decisions only when asked.
- Linear is the only source of task status, priority, owner, due date, and next actions. Do not duplicate them here or in pico.
- For AI features, add versioned evaluation cases, expected behavior, and failure handling before expanding scope.

## Existing project guidance

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
