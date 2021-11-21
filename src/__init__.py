# flake8: noqa

from src import config
from flask import Flask

# setup flask app
app = Flask(__name__)
app.debug = bool(config.DEBUG)

# set endpoints for views
from src import views
