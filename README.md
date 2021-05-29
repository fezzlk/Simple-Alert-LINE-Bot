# Simple-Alert-LINE-Bot
## 動作環境準備
- go のインストール
- (Ginのインストール `$ go get github.com/gin-gonic/gin`)

## 初回起動までの手順
1. LINE Devlopers にてプロバイダ及び messaging API のチャンネルを作っておく
    - 参考: https://developers.line.biz/ja/services/messaging-api/
    - messaging API 設定にて、応答メッセージを無効, webhook URLを有効にする
3. `.env` ファイルにチャンネルトークンとチャンネルシークレットを入力し、コメントアウトを外す
4. `$ go run main.go` // localhost:8080 に立ち上がる
