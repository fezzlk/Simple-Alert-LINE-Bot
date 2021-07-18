package main

import (
    "os"
    "log"
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
}
