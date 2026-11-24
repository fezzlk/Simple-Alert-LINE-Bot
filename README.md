# Simple-Alert-LINE-Bot

## LINE友達追加

<a href="https://lin.ee/Ha5GnFv"><img src="https://scdn.line-apps.com/n/line_add_friends/btn/ja.png" alt="友だち追加" height="36" border="0"></a>

## Features

### アーティストウォッチ

ログイン後、メニューの「アーティストウォッチ」（`/artists`）でアーティスト名・別名・バンド名を追加・編集し、監視を停止・再開できます。登録は1ユーザー30件までです。

- 対象は東京・神奈川・千葉・埼玉。既存の `/_api/v1/check_expire` の毎分実行を利用し、1回のリクエストで1アーティスト、通常は日本時間の毎日9時以降に1日1回チェックします。登録・編集後は次の定期実行で確認します。追加のSchedulerジョブは不要です。
- Billboard Live東京・横浜、Blue Note Tokyo、Cotton Club、SMASH、Creativemanと、任意で登録した公式URL（3件まで）を巡回します。会場サイトの日付・出演者欄、公開ページの構造化イベント情報、公演日・会場が明記された本文を読み取ります。
- 任意の `BRAVE_SEARCH_API_KEY` を設定すると、各アーティストを日本語・英語で1日各1検索し、その他の会場・主催者・チケットサイトも探します。未設定時は公式サイト巡回のみです。検索結果の見出し・要約自体は保存せず、リンク先の公開ページから公演情報を取得します。
- 公演日・会場を確認できる新着、予約開始情報、中止・延期の変更だけをLINE通知します。過去公演や同じ公演の重複掲載は通知しません。OpenAI APIは使用しません。
- 巡回結果・取得失敗・通知保留はWeb画面に表示します。SNS限定・ログイン必須・画像のみの情報、取得を禁止するサイト、未対応のページ構造は検出できません。全公演の網羅を保証する機能ではありません。

#### 無料枠での運用

Brave Searchは**このBot専用のプリペイドプラン**で、前払い残高0ドル、自動入金OFF、追加の有料利用上限0ドルとして設定してください。他用途と共有するキーや既存の後払いプランでは、アプリ内の回数制限だけで無料運用を保証できません。

検索はFirestoreの `artist_watch_usage/YYYY-MM` にHTTP実行前に原子的に予約し、全ユーザー合計でUTC暦月900回に達したら停止します。失敗した検索も予約分に含め、停止後も公式サイト巡回は継続します。API側の残高が先に尽きた場合も、追加購入せず検索が停止する構成にしてください。[Brave料金・無料クレジット](https://api-dashboard.search.brave.com/documentation/pricing)、[プリペイド設定の公式説明](https://api-dashboard.search.brave.com/documentation/resources/help-feedback)。

LINE通知は公式アカウント全体の月間送信数が190通（契約枠がそれ未満ならその枠）に達した時点で保留し、既存の期限・習慣通知向けの余裕を残します。送信結果は通知履歴に保存し、失敗時には同じLINE再送キーで再試行します。LINE連携・Botの友だち登録が必要です。

APIキーの実値はGitに保存せず、ローカルは`.env`、本番は既存のSecret Manager運用で設定してください。本番反映は `cloudbuild.yaml` と既存のCloud Buildトリガーだけを使用します。Cloud Runのリージョン・スケール・CPU設定やSchedulerジョブは、この機能のために変更しません。

## 開発環境準備

- python3 のインストール
- pip3 のインストール
  - pip を最新バージョンにアップデート `python3 -m pip install --upgrade pip`
- ngrok のインストール

## テスト（Firestore Emulator）

1. Emulator 起動
   - `scripts/start_firestore_emulator.sh`（Docker があれば docker-compose を使用）
1. Emulator を使ってテスト実行
   - `scripts/test_with_emulator.sh`

`FIRESTORE_PROJECT_ID` と `FIRESTORE_EMULATOR_HOST` は環境変数で上書きできます。

## Rich Menu 設定

1. Rich Menu 画像（2500x1686）を準備
   - 既定画像: `scripts/assets/rich_menu_default.png`
1. Rich Menu を作成してデフォルト設定
   - `venv/bin/python scripts/setup_line_rich_menu.py`

メニュー割り当て:
- 左上: `一覧`
- 中上: `登録`
- 右上: `使い方`
- 左下: `Web一覧`（`/stock`）
- 中下: `アカウント連携`
- 右下: `習慣タスク`（`/habit`）

## 初回起動および LINE Bot との紐付けまでの手順

1. 仮想環境の作成（必須ではないが推奨）
   `$ python3 -m venv {仮想環境名}`
   `$ source /{仮想環境名}/bin/activate`
1. 依存パッケージのインストール
   `$ pip3 install -r requirements.txt`
1. LINE Devlopers にてプロバイダ及び messaging API のチャンネルを作っておく
   - 参考: https://developers.line.biz/ja/services/messaging-api/
   - messaging API 設定にて、応答メッセージを無効, webhook の利用を有効にする
   - LINE App にて友達登録しておく
1. `.env` ファイルにチャンネルトークンとチャンネルシークレットを入力し、コメントアウトを外す
1. `$ flask run` // localhost:5000 に立ち上がる
1. ngrok コマンドにて 5000 ポートをデプロイ
   - `$ ngrok http 5000`
1. デプロイ先の URL の末尾に `/callback` を追加し、LINE bot チャンネルの Webhook URL に設定

## 2 回目以降の起動

1. `$ flask run`
1. `$ ngrok http 5000`
1. 発行された URL の末尾に `/callback` を追加し、　 LINE bot チャンネルの Webhook URL に設定

## 処理の流れ

### 起動

1. `$ flask run` を実行すると、`server.py` に書かれた処理が実行される。
1. その中で `src/__init__.py` の app を取得し、`app.run()` が呼び出されることでサーバーが起動する。

### LINE アプリでのメッセージ受信時

1. bot 宛にメッセージが送信されると、 `/callback` (LINE bot チャンネルの WebhookURL に基づいたエンドポイント) に POST リクエストが送信される。
1. そのリクエストをサーバーが受け取り、`src/views.py` の callback() が実行される。
1. handler.handle(body, signature) によりイベントをハンドリングする。
1. ハンドリングしたイベントに対応した、`handler.add()` によりハンドラーに登録されている関数が実行される
