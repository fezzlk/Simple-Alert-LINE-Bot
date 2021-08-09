import config

# setup for flask
from flask import Flask

app = Flask(__name__)
app.debug = bool(config.DEBUG)

# setup for line-bot-sdk
from linebot import (LineBotApi, WebhookHandler)
line = LineBotApi(config.LINEBOT_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINEBOT_CHANNEL_SECRET)

# set endpoints for views
from src import views
