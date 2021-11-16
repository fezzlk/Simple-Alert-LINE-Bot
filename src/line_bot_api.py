import config
from linebot import (LineBotApi, WebhookHandler)

# setup for line-bot-sdk
line_bot_api = LineBotApi(config.LINEBOT_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINEBOT_CHANNEL_SECRET)
