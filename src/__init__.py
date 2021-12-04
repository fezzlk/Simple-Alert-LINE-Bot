# flake8: noqa

from src import config
from flask import Flask
from flask_assets import Environment, Bundle
from src.routes.views import views_blueprint
from src.routes.api import api_blueprint
from src.routes.handle_line_event import line_blueprint
from src.oauth_client import oauth
from src.middlewares.WerkzeugMiddleware import WerkzeugMiddleware

# setup flask app
app = Flask(__name__)
app.debug = bool(config.DEBUG)
app.secret_key = 'random secret'
oauth.init_app(app)

# set endpoints for views
app.register_blueprint(views_blueprint)
app.register_blueprint(api_blueprint)
app.register_blueprint(line_blueprint)

# set middleware
app.wsgi_app = WerkzeugMiddleware(app.wsgi_app)

# scss
assets = Environment(app)
assets.url = app.static_url_path
scss = Bundle('scss/style.scss', filters='pyscss', output='all.css')
assets.register('scss_all', scss)
