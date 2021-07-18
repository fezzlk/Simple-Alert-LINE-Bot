package main

import (
    "os"
    "log"
    "strings"
    "github.com/gin-gonic/gin"
    "github.com/joho/godotenv"
    "github.com/line/line-bot-sdk-go/linebot"
    "main.go/scraping"
)

func main() {
    // 環境変数の取得
    dotEnvErr := godotenv.Load()
    if dotEnvErr != nil {
      log.Fatal("Error loading .env file")
    }

    // bot を用意
    bot, botErr := linebot.New(
        os.Getenv("LINEBOT_CHANNEL_SECRET"),
        os.Getenv("LINEBOT_CHANNEL_TOKEN"),
    )
    if botErr != nil {
        log.Fatal(botErr)
    }
    
    // 定期イベント
    if len(os.Args) >= 2 && os.Args[1] == "7pm" {
        // https://transit.yahoo.co.jp/traininfo/top より各路線の運行情報が
        // 記載されたページのURLを取得
        trainInfo := ""
        data := ""

        // 京浜東北根岸線
        url := "https://transit.yahoo.co.jp/traininfo/detail/22/0/"
        data = scraping.GetTrainInfo(url)
        trainInfo += "京浜東北根岸線:\n" + data + "\n"
        // if data != "遅延はありません。" {
        // 	trainInfo += "京浜東北根岸線:\n" + data + "\n"
        // }

        // 横須賀線
        url = "https://transit.yahoo.co.jp/traininfo/detail/29/0/"
        data = scraping.GetTrainInfo(url)
        trainInfo += "横須賀線:\n" + data
        // 	if data != "遅延はありません。" {
        // 	trainInfo += "横須賀線:\n" + data
        // }

        if trainInfo != "" {
            _, err := bot.BroadcastMessage(linebot.NewTextMessage(trainInfo)).Do()
            if err != nil {
                log.Fatal(err)
            }
        }
    } else {
        // gin サーバーの準備
        router := gin.Default()
        router.Use(gin.Logger())
        router.LoadHTMLGlob("templates/*.html")

        // ルートパスでの処理(ホームページの表示)
        router.GET("/", func(ctx *gin.Context){
            ctx.HTML(200, "index.html", gin.H{})
        })

        // LINE Messaging API のリクエスト
        router.POST("/callback", func(c *gin.Context) {
            events, err := bot.ParseRequest(c.Request)
            if err != nil {
                if err == linebot.ErrInvalidSignature {
                    log.Print(err)
                }
                return
            }

            // "可愛い" 単語を含む場合、返信される
            var keywordForTextResponse string
            keywordForTextResponse = "可愛い"

            // チャットの回答
            var response string
            response = "ありがとう！！"

            // "おはよう" 単語を含む場合、返信される
            var keywordForStickerResponse string
            keywordForStickerResponse = "おはよう"

            // スタンプで回答が来る
            responseSticker := linebot.NewStickerMessage("11537", "52002757")

            // "猫" 単語を含む場合、返信される
            var keywordForImageResponse string
            keywordForImageResponse = "猫"

            // 猫の画像が表示される
            responseImage := linebot.NewImageMessage("https://i.gyazo.com/2db8f85c496dd8f21a91eccc62ceee05.jpg", "https://i.gyazo.com/2db8f85c496dd8f21a91eccc62ceee05.jpg")

            // "ディズニー" 単語を含む場合、返信される
            var keywordForLocationResponse string
            keywordForLocationResponse = "ディズニー"

            // ディズニーが地図表示される
            responseLocation := linebot.NewLocationMessage("東京ディズニーランド", "千葉県浦安市舞浜", 35.632896, 139.880394)

            // 遅延情報を返信
            var keywordForTrainInfoResponse string
            keywordForTrainInfoResponse = "遅延"

            // https://transit.yahoo.co.jp/traininfo/top より各路線の運行情報が
            // 記載されたページのURLを取得
            trainInfo := ""

            // 京浜東北根岸線
            url := "https://transit.yahoo.co.jp/traininfo/detail/22/0/"
            trainInfo += "京浜東北根岸線:\n" + scraping.GetTrainInfo(url) + "\n"

            // 横須賀線
            url = "https://transit.yahoo.co.jp/traininfo/detail/29/0/"
            trainInfo += "横須賀線:\n" + scraping.GetTrainInfo(url)


            for _, event := range events {
                // イベントがメッセージの受信だった場合
                if event.Type == linebot.EventTypeMessage {
                    switch message := event.Message.(type) {
                    // メッセージがテキスト形式の場合
                    case *linebot.TextMessage:
                        receivedMessage := message.Text
                        // テキストで返信されるケース
                        if strings.Contains(receivedMessage, keywordForTextResponse) {
                            bot.ReplyMessage(event.ReplyToken, linebot.NewTextMessage(response)).Do()
                            // スタンプで返信されるケース
                        } else if strings.Contains(receivedMessage, keywordForStickerResponse) {
                            bot.ReplyMessage(event.ReplyToken, responseSticker).Do()
                            // 画像で返信されるケース
                        } else if strings.Contains(receivedMessage, keywordForImageResponse) {
                            bot.ReplyMessage(event.ReplyToken, responseImage).Do()
                            // 地図表示されるケース
                        } else if strings.Contains(receivedMessage, keywordForLocationResponse) {
                            bot.ReplyMessage(event.ReplyToken, responseLocation).Do()
                            // 電車遅延情報を返信
                        } else if strings.Contains(receivedMessage, keywordForTrainInfoResponse) {
                            bot.ReplyMessage(event.ReplyToken, linebot.NewTextMessage(trainInfo)).Do()
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
        router.Run()
    }
}
