# Simple-Alert-LINE-Bot
## 動作環境準備
- go のインストール
- (Ginのインストール `$ go get github.com/gin-gonic/gin`)

## 初回起動までの手順
1. LINE Devlopers にてプロバイダ及び messaging API のチャンネルを作っておく
1. `.env` ファイルにチャンネルトークンとチャンネルシークレットを入力
1. `$ go run main.go` // localhost:8080 に立ち上がる
