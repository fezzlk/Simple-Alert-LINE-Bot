# flake8: noqa

from src import config
from flask import Flask
from src.views import views_blueprint

# setup flask app
app = Flask(__name__)
app.debug = bool(config.DEBUG)

# set endpoints for views
app.register_blueprint(views_blueprint)
