package main

import (
	"log"
	"net/http"

	"github.com/line/line-bot-sdk-go/v7/linebot"
	"github.com/line/line-bot-sdk-go/v7/linebot/httphandler"
)

func main() {

	// LineDeveloperからSECTET、TOKEN取得して書き換え
	handler, err := httphandler.New(
		"CHANNEL_SECRET",
		"CHANNEL_TOKEN",
	)
	if err != nil {
		log.Fatal(err)
	}

	// LINEイベント
	handler.HandleEvents(func(events []*linebot.Event, r *http.Request) {
		bot, err := handler.NewClient()
		if err != nil {
			log.Print(err)
			return
		}
		for _, event := range events {
			if event.Type == linebot.EventTypeMessage {
				switch message := event.Message.(type) {
				case *linebot.TextMessage:
					if _, err = bot.ReplyMessage(event.ReplyToken, linebot.NewTextMessage(message.Text)).Do(); err != nil {
						log.Print(err)
					}
				}
			}
		}
	})
	http.Handle("/callback", handler)

	// SSL証明書の場所を記述
	if err := http.ListenAndServeTLS(
		"",
		"",
		"", nil); err != nil {
		logger.Fatal("ListenANdServe:", err)
	}
}
