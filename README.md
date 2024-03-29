# Simple-Alert-LINE-Bot

## LINE友達追加

<a href="https://lin.ee/Ha5GnFv"><img src="https://scdn.line-apps.com/n/line_add_friends/btn/ja.png" alt="友だち追加" height="36" border="0"></a>

## Features

TBD

## 開発環境準備

- python3 のインストール
- pip3 のインストール
  - pip を最新バージョンにアップデート `python3 -m pip install --upgrade pip`
- ngrok のインストール

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
