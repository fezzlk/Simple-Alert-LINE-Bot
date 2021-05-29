package main

import (
    "os"
    "log"
    "strings"
    "github.com/gin-gonic/gin"
    "github.com/joho/godotenv"
    "github.com/line/line-bot-sdk-go/linebot"
)

func main() {
    dotEnvErr := godotenv.Load()
    if dotEnvErr != nil {
      log.Fatal("Error loading .env file")
    }
    bot, botErr := linebot.New(
        os.Getenv("LINEBOT_CHANNEL_SECRET"),
        os.Getenv("LINEBOT_CHANNEL_TOKEN"),
    )
    if botErr != nil {
        log.Fatal(botErr)
    }
      
    router := gin.Default()
    router.Use(gin.Logger())
    router.LoadHTMLGlob("templates/*.html")

    router.GET("/", func(ctx *gin.Context){
        ctx.HTML(200, "index.html", gin.H{})
    })

    // LINE Messaging API ルーティング
	router.POST("/callback", func(c *gin.Context) {
		events, err := bot.ParseRequest(c.Request)
		if err != nil {
			if err == linebot.ErrInvalidSignature {
				log.Print(err)
			}
			return
		}

		// "可愛い" 単語を含む場合、返信される
		var replyText string
		replyText = "可愛い"

		// チャットの回答
		var response string
		response = "ありがとう！！"

		// "おはよう" 単語を含む場合、返信される
		var replySticker string
		replySticker = "おはよう"

		// スタンプで回答が来る
		responseSticker := linebot.NewStickerMessage("11537", "52002757")

		// "猫" 単語を含む場合、返信される
		var replyImage string
		replyImage = "猫"

		// 猫の画像が表示される
		responseImage := linebot.NewImageMessage("https://i.gyazo.com/2db8f85c496dd8f21a91eccc62ceee05.jpg", "https://i.gyazo.com/2db8f85c496dd8f21a91eccc62ceee05.jpg")

		// "ディズニー" 単語を含む場合、返信される
		var replyLocation string
		replyLocation = "ディズニー"

		// ディズニーが地図表示される
		responseLocation := linebot.NewLocationMessage("東京ディズニーランド", "千葉県浦安市舞浜", 35.632896, 139.880394)

		for _, event := range events {
			// イベントがメッセージの受信だった場合
			if event.Type == linebot.EventTypeMessage {
				switch message := event.Message.(type) {
				// メッセージがテキスト形式の場合
				case *linebot.TextMessage:
					replyMessage := message.Text
					// テキストで返信されるケース
					if strings.Contains(replyMessage, replyText) {
						bot.ReplyMessage(event.ReplyToken, linebot.NewTextMessage(response)).Do()
						// スタンプで返信されるケース
					} else if strings.Contains(replyMessage, replySticker) {
						bot.ReplyMessage(event.ReplyToken, responseSticker).Do()
						// 画像で返信されるケース
					} else if strings.Contains(replyMessage, replyImage) {
						bot.ReplyMessage(event.ReplyToken, responseImage).Do()
						// 地図表示されるケース
					} else if strings.Contains(replyMessage, replyLocation) {
						bot.ReplyMessage(event.ReplyToken, responseLocation).Do()
					}
					// 上記意外は、おうむ返しで返信
					_, err = bot.ReplyMessage(event.ReplyToken, linebot.NewTextMessage(replyMessage)).Do()
					if err != nil {
						log.Print(err)
					}
				}
			}
		}
	})
    router.Run()
}
// hoge