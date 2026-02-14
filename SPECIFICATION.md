# Simple-Alert-LINE-Bot 仕様書（コード起点）

最終更新: 2026-02-14  
対象コード: `src/` 配下（LINE Bot / Web / Firestore 実装）

## 1. システム概要

- 目的
  - もの・タスクの期限を登録し、一覧管理と期限通知を行う。
- 提供チャネル
  - LINE 個人チャット（自然文入力）
  - Web 画面（一覧/追加/更新/削除/復元）
- 永続化
  - Firestore（本番）
  - Firestore Emulator（ローカル結合テスト）

## 2. 機能仕様

### 2.1 LINE（チャット）

- Webhook: `POST /callback`
- 主な機能
  - 友だち追加時メッセージ送信
  - 自然文からの登録/更新/削除/ガイド/一覧/Web/ログイン意図推定
  - 実行前確認（「はい / いいえ」 or postback）
  - 一覧表示トリガー（例: `一覧表示`, `リスト表示`）
  - Web リンク返信トリガー（例: `webで操作`, `webで表示`）
  - 使い方ガイド返信トリガー（例: `使い方`, `使い方教えて`, `何ができる`）
  - ログイントリガー（例: `ログイン`, `webにログイン`, `サインイン`）

- 意図推定
  - `OPENAI_API_KEY` がある場合: OpenAI Chat Completions で JSON 解析
  - ない場合: 正規表現ベースのフォールバック解析
  - 出力スキーマ: `intent`, `item_name`, `expiry_date`
  - `intent` は `register|update|delete|help|list|web|login|none`
  - `expiry_date` は `YYYY-MM-DD` のみ許可
  - `help/list/web/login` は非CRUDのため確認フローなしで該当ユースケースへルーティング

- 安全制御
  - 一括操作文言（例: 全部削除）を `none` 判定
  - プロンプト注入系文言（例: system prompt 表示要求）を `none` 判定
  - 不確実な相対日付（来週/再来週など）は `none` 判定
  - すべて確認フェーズを通過しない限り実行しない

- 実行確認フロー
  1. ユーザー文を解析
  2. Firestore `line_pending_operations` に保留操作保存
  3. 「実行しますか？」ボタン返信
  4. `はい` / `intent_confirm:yes` で確定実行
  5. `いいえ` / `intent_confirm:no` でキャンセル
  6. 期限なしで登録した場合は、続けて期限設定を提案（例: `15日で`, `明日で`, `3/15で`）

- 期限なし登録の直後フォロー
  - 対象: 期限なしで登録確定した直後の同一ユーザー
  - 入力例: `じゃあ15日で`, `明日で`, `3/15で`, `2026-03-15で`
  - `なし/不要/いらない` で期限未設定のまま終了
  - 更新対象は「直前に登録した同名の active アイテム（最新1件）」

### 2.2 LINE（定期通知）

- API: `POST /_api/v1/check_expire`
- スケジューラ想定（GCP）
  - Cloud Scheduler から日次実行
  - 実行時刻: 毎日 12:00（JST）
  - cron 例: `0 12 * * *`
  - timezone: `Asia/Tokyo`
- 処理
  - LINE ユーザーごとに `status=1` のアイテムを取得
  - アイテムが1件以上あるユーザーにのみ push 通知
  - まず Web 一覧 URL を通知
  - 続けて、期限が3日以内（当日/翌日/3日後まで）のものだけを通知
  - 期限切れ/期限なし/4日以上先はこの定期通知では通知しない

### 2.3 Web

- 画面
  - `/` トップ
  - `/stock` 一覧（要ログイン）
  - `/stock` POST 追加
  - `/stock/update` POST 更新
  - `/stock/delete` POST 論理削除
  - `/stock/delete` GET ゴミ箱
  - `/stock/restore` POST 復元
  - `/stock/complete_delete` POST 物理削除
  - `/register` ユーザー登録
  - `/line/login`, `/line/authorize` LINE OAuth ログイン
  - `/line/approve` LINE 連携承認
  - `/line/register` LINE 由来ユーザー登録

- 認証
  - `login_required` で `session['login_user']` を必須化
  - 未ログイン時は `/line/login` へリダイレクト
  - 開発時 (`FLASK_ENV=development`) は `/login` ローカル認証を利用可能

## 3. データ仕様（Firestore）

### 3.1 `stocks`

- 主な項目
  - `_id`（Doc ID）
  - `item_name: str`
  - `owner_id: str`（LINE user id または Web user id）
  - `expiry_date: datetime | null`
  - `status: int`（`1=active`, `2=archived` 運用）
  - `created_at`, `updated_at`

### 3.2 `line_users`

- 主な項目
  - `_id`
  - `line_user_name`
  - `line_user_id`
  - `created_at`, `updated_at`

### 3.3 `web_users`

- 主な項目
  - `_id`
  - `web_user_name`
  - `web_user_email`
  - `linked_line_user_id`
  - `is_linked_line_user`
  - `created_at`, `updated_at`

### 3.4 `line_pending_operations`

- 主な項目
  - `line_user_id`
  - `operation`（`intent`, `item_name`, `expiry_date`）
  - `updated_at`

## 4. 入力ルール（自然文）

- 登録例
  - `卵は3/15まで`
  - `ライブチケット購入 3/20まで`
  - `打ち合わせ日程調整 2/28まで`
- 更新例
  - `卵の期限を3/22にして`
  - `更新 卵 2026-03-22`
- 削除例
  - `卵を使い切った`
  - `卵 削除`
- 一覧/リンク
  - `一覧表示` / `リスト表示`
  - `webで操作` / `webで表示`
- ログイン導線
  - `ログイン` / `webにログイン` / `サインイン`
- 使い方
  - `使い方` / `使い方教えて` / `何ができる`

## 5. 主要環境変数

- LINE
  - `LINEBOT_CHANNEL_SECRET`
  - `LINEBOT_CHANNEL_ACCESS_TOKEN`
  - `LINE_LOGIN_CHANNEL_ID`
  - `LINE_LOGIN_CHANNEL_SECRET`
- OpenAI
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`（default: `gpt-4o-mini`）
- Firestore
  - `FIRESTORE_PROJECT_ID`
  - `FIRESTORE_EMULATOR_HOST`（ローカル時）
- App
  - `SERVER_URL`
  - `FLASK_ENV`
  - `LOCAL_AUTH_USER_CODE`, `LOCAL_AUTH_PASSWORD`（開発ログイン）

## 6. 運用・テスト方針（リポジトリルール）

- Cloud Run
  - project_id: `simple-alert-line-bot`
  - service_name: `simple-alert-line-bot`
- テスト
  - `venv` を利用
  - ローカル結合テストは Firestore Emulator を利用

## 7. 既知の仕様上メモ

- 自然文優先で運用しているが、互換のため一部明示キーワード（`登録`, `一覧`, `URL`, `アカウント連携`）ルートは残っている。
- `ログイン` 系メッセージは `URL` 返信（`/stock?openExternalBrowser=1`）へルーティングする。
- 保留操作 (`line_pending_operations`) に TTL は未実装。
- 日付の曖昧表現（来週など）は安全優先で実行不可。
