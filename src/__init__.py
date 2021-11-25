# flake8: noqa

from src import config
from flask import Flask
from flask_assets import Environment, Bundle
from src.views import views_blueprint
from src.handle_line_event import line_blueprint

# setup flask app
app = Flask(__name__)
app.debug = bool(config.DEBUG)

# set endpoints for views
app.register_blueprint(views_blueprint)
app.register_blueprint(line_blueprint)

# scss
assets = Environment(app)
assets.url = app.static_url_path
scss = Bundle('scss/style.scss', filters='pyscss', output='all.css')
assets.register('scss_all', scss)
