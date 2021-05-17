package main

import (
    "os"
    "log"
    "github.com/gin-gonic/gin"
    "github.com/joho/godotenv"
    "github.com/line/line-bot-sdk-go/linebot"
)

func main() {
    dotEnvErr := godotenv.Load()
    if dotEnvErr != nil {
      log.Fatal("Error loading .env file")
    }
    _, botErr := linebot.New(
        os.Getenv("LINEBOT_CHANNEL_SECRET"),
        os.Getenv("LINEBOT_CHANNEL_TOKEN"),
    )
    if botErr != nil {
        log.Fatal(botErr)
    }
      
    router := gin.Default()
    router.LoadHTMLGlob("templates/*.html")

    router.GET("/", func(ctx *gin.Context){
        ctx.HTML(200, "index.html", gin.H{})
    })

    router.Run()
}