# Simple-Alert-LINE-Bot

## 動作環境準備
- go のインストール
- (Ginのインストール `$ go get github.com/gin-gonic/gin`)
- ngrok のインストール

## 初回起動およびLINE Botとの紐付けまでの手順
1. LINE Devlopers にてプロバイダ及び messaging API のチャンネルを作っておく
    - 参考: https://developers.line.biz/ja/services/messaging-api/
    - messaging API 設定にて、応答メッセージを無効, webhookの利用を有効にする
    - LINE App にて友達登録しておく
1. `.env` ファイルにチャンネルトークンとチャンネルシークレットを入力し、コメントアウトを外す
1. `$ go run main.go` // localhost:8080 に立ち上がる
1. ngrok コマンドにて8080ポートをデプロイ
    - `$ ngrok http 8080`
1. デプロイ先の URL の末尾に `/callback` を追加し、LINE bot チャンネルの Webhook URL に設定

## 2回目以降の起動
1. `$ go run main.go`
1. `$ ngrok http 8080`
1. 発行された URL の末尾に `/callback` を追加し、　LINE bot チャンネルの Webhook URL に設定
