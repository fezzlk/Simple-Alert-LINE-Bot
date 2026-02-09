from src import config
from authlib.integrations.flask_client import OAuth


oauth = OAuth()
oauth.register(
    name='line',
    client_id=config.LINE_LOGIN_CHANNEL_ID,
    client_secret=config.LINE_LOGIN_CHANNEL_SECRET,
    server_metadata_url='https://access.line.me/.well-known/openid-configuration',
    access_token_url='https://api.line.me/oauth2/v2.1/token',
    authorize_url='https://access.line.me/oauth2/v2.1/authorize',
    api_base_url='https://api.line.me/',
    client_kwargs={'scope': 'profile openid'},
)
