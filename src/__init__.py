# flake8: noqa

import config
from flask import Flask
from linebot import (LineBotApi, WebhookHandler)
from .pymongo import mongo_client

# setup flask app
app = Flask(__name__)
app.debug = bool(config.DEBUG)

# setup connection to mongodb
app.config["MONGO_URI"] = config.MONGO_URI
mongo_client.init_app(app)

# setup for line-bot-sdk
line = LineBotApi(config.LINEBOT_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINEBOT_CHANNEL_SECRET)

# set endpoints for views
from src import views
