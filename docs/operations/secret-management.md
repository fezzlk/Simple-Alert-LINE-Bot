# シークレット管理・削除運用（商用β向け）

最終更新: 2026-07-20 / 関連: Linear FEZ-13, FEZ-5

本サービス remily が扱うシークレットと個人データの管理・削除運用をまとめる。規約・プライバシーポリシーの記載と本ドキュメント・実装が一致していることを公開前に確認する。

## 1. シークレット一覧

| 変数 | 用途 | 必須 | 保管 |
|------|------|------|------|
| `FLASK_SECRET_KEY` | Flask セッション署名 | 本番必須 | Secret Manager / 環境変数 |
| `API_KEY_ENCRYPTION_KEY` | ユーザー登録の OpenAI APIキー暗号化鍵 | 本番必須（未設定だと暗号化失敗） | Secret Manager / 環境変数 |
| `LINEBOT_CHANNEL_SECRET` / `LINEBOT_CHANNEL_ACCESS_TOKEN` | LINE Messaging API | 本番必須 | Secret Manager / 環境変数 |
| `LINE_LOGIN_CHANNEL_ID` / `LINE_LOGIN_CHANNEL_SECRET` | LINE ログイン | 必須 | Secret Manager / 環境変数 |
| `OPENAI_API_KEY` | 共通の意図解析キー（ユーザー未設定時のフォールバック） | 任意 | Secret Manager / 環境変数 |
| `INTERNAL_API_KEY` | 内部API（通知バッチ）保護 | 推奨 | Secret Manager / 環境変数 |

- `.env.example` に全キーのプレースホルダーを記載する。実値は `.env`（Git 管理外）または Cloud Run のシークレット参照で注入する。
- `.env` の変更は CI（`deny-env-change.yml`）でブロックされる。実値をコミットしないこと。

## 2. OpenAI APIキー暗号化の仕組みと制約

- 実装: `src/services/encryption.py`（Fernet + PBKDF2HMAC）。ユーザーが設定画面で登録した APIキーを暗号化して `web_users.encrypted_openai_api_key` に保存する。平文はDBに保存しない。
- 鍵導出: `API_KEY_ENCRYPTION_KEY` を PBKDF2 で伸長。
- **既知の制約（要改善）**: ソルトがソースにハードコード（`_SALT = b"remily-api-key-encryption-salt"`）。将来的には環境変数化するか、ユーザー単位ソルトの導入を検討する。有料化前に見直す。

## 3. 鍵ローテーション手順

`API_KEY_ENCRYPTION_KEY` を変更すると既存の暗号化済みキーは復号できなくなる。ローテーション時は以下のいずれか。

1. 単純運用（β推奨）: 新鍵に切り替え、全ユーザーの `encrypted_openai_api_key` を無効化（null 化）し、再登録を案内する。
2. 無停止運用（将来）: 旧鍵で復号 → 新鍵で再暗号化する移行スクリプトを用意してから切り替える。

いずれの場合も、切替前に現行の暗号化データをバックアップする。

## 4. 漏えい時対応

1. 影響範囲の特定（どの鍵/データが漏えいしたか）。
2. 該当シークレットを即時ローテーション（LINE トークン・`API_KEY_ENCRYPTION_KEY` 等）。
3. `API_KEY_ENCRYPTION_KEY` 漏えい時は、暗号化済み OpenAI キーが復号され得るため、全ユーザーの登録キーを無効化し再登録を案内。ユーザーには OpenAI 側でのキー失効も案内する。
4. 個人データ漏えいの可能性がある場合、個人情報保護法に基づく本人通知・個人情報保護委員会への報告要否を判断する。
5. 事象・対応をこのリポジトリの `docs/` またはインシデント記録に残す。

## 5. 退会・データ削除運用

- Web ログインユーザー: 設定画面「退会（アカウント削除）」から自己完結で即時削除（`WithdrawAccountUseCase`）。削除対象は下記の全コレクション。
- LINE 専用（Web 未ログイン）ユーザー: LINE公式アカウントのブロック、または問い合わせ窓口経由で申請 → 運営が手動削除。**原則、申請から30日以内**。
- 手動削除時に対象とするコレクション:
  - `stocks` / `habit_tasks` / `habit_task_logs`（`owner_id` = LINE または Web のユーザーID）
  - `habit_pending_confirmations`（`owner_id` / `line_user_id`）
  - `line_pending_operations`（doc id = `line_user_id`）
  - `notification_schedules`（doc id = `line_user_id`）
  - `line_users`（`line_user_id`）/ `web_users`（`_id`）

## 6. 法務専門家への確認要否

- 無料βの現段階では、特定商取引法（有償取引が前提）の表記義務は生じないため、専門家レビューは任意と判断する。提供者名はハンドル名で運用可。
- **有料化する場合は**、公開前に以下を実施する:
  - 特商法に基づく事業者名（原則実名）・所在地・連絡先の表示。
  - 利用規約・プライバシーポリシーの専門家レビュー（免責範囲、越境データ移転、返金・解約条項等）。

## 7. 公開前チェックリスト

- [ ] `SERVICE_PROVIDER_NAME` を確定（β: `fezzlk`）。
- [ ] `CONTACT_FORM_URL` に実フォームURLを設定（未設定だと規約/PPはLINEトーク案内にフォールバック）。
- [ ] `FLASK_SECRET_KEY` / `API_KEY_ENCRYPTION_KEY` を本番シークレットとして設定。
- [ ] `/terms` `/privacy` の表示にプレースホルダーが残っていないことを確認。
- [ ] 退会フロー（設定画面）が動作することを確認。
