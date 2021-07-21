package main

import (
    "os"
    "log"
    "strings"
    "github.com/gin-gonic/gin"
    "github.com/joho/godotenv"
    "github.com/line/line-bot-sdk-go/linebot"
    "main.go/trainInfo"
    "main.go/weather"
)

func main() {
    // 環境変数の取得
    dotEnvErr := godotenv.Load()
    if dotEnvErr != nil {
      log.Fatal("Error loading .env file")
    }

    // line bot sdk for go の linebot の利用
    bot, botErr := linebot.New(
        os.Getenv("LINEBOT_CHANNEL_SECRET"),
        os.Getenv("LINEBOT_CHANNEL_TOKEN"),
    )
    if botErr != nil {
        log.Fatal(botErr)
    }
    
    // 定期イベント(heroku scheduler で go コマンドによる起動ができないため、ここに記述し、コマンドライン引数の有無で実行を制御)
    // see. https://stackoverflow.com/questions/39172378/using-heroku-scheduler-add-on-with-golang-app
    if len(os.Args) >= 2 {
        if os.Args[1] == "check_train" {
            // 電車遅延情報を取得し、遅延があった場合のみプッシュ通知する
            data := trainInfo.GetTrainInfoMap();
            trainInfoText := ""
            for key, value := range data {
                if value != "遅延はありません。" {
                    trainInfoText += key + ":\n" + value + "\n"
                }
            }
            if trainInfoText != "" {
                _, err := bot.BroadcastMessage(linebot.NewTextMessage(trainInfoText)).Do()
                if err != nil {
                    log.Fatal(err)
                }
            }
        }
    } else { // コマンドライン引数がない場合はサーバー起動
        // gin サーバーの準備
        router := gin.Default()
        router.Use(gin.Logger())
        router.LoadHTMLGlob("templates/*.html")

        // ルートパスでの処理(ホームページの表示)
        router.GET("/", func(ctx *gin.Context){
            ctx.HTML(200, "index.html", gin.H{})
        })

        // LINE Messaging API 用のエンドポイント
        router.POST("/callback", func(c *gin.Context) {
            // リクエストから LINE イベント(LINEユーザーが操作した内容)を取得
            events, err := bot.ParseRequest(c.Request)
            if err != nil {
                if err == linebot.ErrInvalidSignature {
                    log.Print(err)
                }
                return
            }

            // キーワードを定義（ユーザーが送信したメッセージに以下のキーワードが含まれていた場合対応した返事をする)
            keywordForTextResponse := "可愛い" // テキスト返信用
            keywordForStickerResponse := "おはよう" // スタンプ返信用
            keywordForImageResponse := "猫" // 画像返信用
            keywordForLocationResponse := "ディズニー" // 地図表示用
            keywordForTrainInfoResponse := "遅延" // 電車遅延情報返信用
            keywordForWeatherResponse := "天気" // 天気情報返信用

            // 返信内容を定義
            responseText := "ありがとう！！" // テキスト
            responseSticker := linebot.NewStickerMessage("11537", "52002757") // スタンプ
            responseImage := linebot.NewImageMessage("https://i.gyazo.com/2db8f85c496dd8f21a91eccc62ceee05.jpg", "https://i.gyazo.com/2db8f85c496dd8f21a91eccc62ceee05.jpg") // 画像
            responseLocation := linebot.NewLocationMessage("東京ディズニーランド", "千葉県浦安市舞浜", 35.632896, 139.880394) // 地図
            // 電車遅延情報
            data := trainInfo.GetTrainInfoMap()
            trainInfoText := ""
            for key, value := range data {
                trainInfoText += key + ":\n" + value + "\n"
            }
            // 天気情報
            weatherInfoStr := "" 
            for _, r := range weather.GetWeather() {
                weatherInfoStr += r.Date + r.Weather + "\n"
            }

            for _, event := range events {
                // イベントがメッセージの受信だった場合
                if event.Type == linebot.EventTypeMessage {
                    switch message := event.Message.(type) {
                    // メッセージがテキスト形式の場合
                    case *linebot.TextMessage:
                        receivedMessage := message.Text
                        if strings.Contains(receivedMessage, keywordForTextResponse) {
                            // テキストを返信
                            bot.ReplyMessage(event.ReplyToken, linebot.NewTextMessage(responseText)).Do()
                        } else if strings.Contains(receivedMessage, keywordForStickerResponse) {
                            // スタンプを返信
                            bot.ReplyMessage(event.ReplyToken, responseSticker).Do()
                        } else if strings.Contains(receivedMessage, keywordForImageResponse) {
                            // 画像を返信
                            bot.ReplyMessage(event.ReplyToken, responseImage).Do()
                        } else if strings.Contains(receivedMessage, keywordForLocationResponse) {
                            // 地図を返信
                            bot.ReplyMessage(event.ReplyToken, responseLocation).Do()
                        } else if strings.Contains(receivedMessage, keywordForTrainInfoResponse) {
                            // 電車遅延情報を返信
                            bot.ReplyMessage(event.ReplyToken, linebot.NewTextMessage(trainInfoText)).Do()
                        } else if strings.Contains(receivedMessage, keywordForWeatherResponse) {
                            // 天気情報を返信
                            bot.ReplyMessage(event.ReplyToken, linebot.NewTextMessage(weatherInfoStr)).Do()
                        }
                        // 上記以外は、おうむ返しで返信
                        _, err = bot.ReplyMessage(event.ReplyToken, linebot.NewTextMessage(receivedMessage)).Do()
                        if err != nil {
                            log.Print(err)
                        }
                    }
                }
            }
        })

        // サーバー起動
        router.Run()
    }
}
