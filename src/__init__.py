# flake8: noqa

import config
from flask import Flask
from .pymongo import mongo_client

# setup flask app
app = Flask(__name__)
app.debug = bool(config.DEBUG)

# setup connection to mongodb
app.config["MONGO_URI"] = config.MONGO_URI
mongo_client.init_app(app)

# set endpoints for views
from src import views
