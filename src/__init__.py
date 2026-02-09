# flake8: noqa

from src import config
import logging
from flask import Flask, session
from webassets import Environment, Bundle
from webassets.ext.jinja2 import AssetsExtension
from src.routes.views import views_blueprint
from src.routes.api import api_blueprint
from src.routes.handle_line_event import line_blueprint
from src.oauth_client import oauth
from src.middlewares.WerkzeugMiddleware import WerkzeugMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix
from src.web_context import build_login_user

# setup flask app
app = Flask(__name__)
app.debug = bool(config.DEBUG)
app.secret_key = 'random secret'
oauth.init_app(app)
if config.IS_DEVELOPMENT:
    logging.warning(
        'FLASK_ENV is development. Production deploys should set FLASK_ENV=production.'
    )

# set endpoints for views
app.register_blueprint(views_blueprint)
app.register_blueprint(api_blueprint)
app.register_blueprint(line_blueprint)

# set middleware
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
app.wsgi_app = WerkzeugMiddleware(app.wsgi_app)

# scss
assets = Environment(directory=app.static_folder, url=app.static_url_path)
assets.register('scss_all', Bundle('scss/style.scss', filters='libsass', output='all.css'))
app.jinja_env.add_extension(AssetsExtension)
app.jinja_env.assets_environment = assets


@app.context_processor
def inject_login_url():
    if config.IS_DEVELOPMENT:
        login_url = '/line/login'
    elif config.SERVER_URL:
        login_url = f'{config.SERVER_URL.rstrip("/")}/line/login'
    else:
        login_url = '/line/login'
    return {
        'login_url': login_url,
        'login_user': build_login_user(session),
    }
