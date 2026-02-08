# flake8: noqa

from src import config
from flask import Flask
from webassets import Environment, Bundle
from webassets.ext.jinja2 import AssetsExtension
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
assets = Environment(directory=app.static_folder, url=app.static_url_path)
assets.register('scss_all', Bundle('scss/style.scss', filters='libsass', output='all.css'))
app.jinja_env.add_extension(AssetsExtension)
app.jinja_env.assets_environment = assets


@app.context_processor
def inject_login_url():
    if config.IS_DEVELOPMENT:
        return {'login_url': '/line/login'}
    if config.SERVER_URL:
        return {'login_url': f'{config.SERVER_URL.rstrip("/")}/line/login'}
    return {'login_url': '/line/login'}
