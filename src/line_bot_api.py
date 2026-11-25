from src import config
from linebot.v3.messaging import ApiClient, Configuration, MessagingApi, MessagingApiBlob
from linebot.v3.webhook import WebhookHandler

# setup for line-bot-sdk
# トークン未設定（CI・テスト・.env 無しのローカル等）でも import 時に
# linebot SDK が None を連結して落ちないよう、ダミー値でフォールバックする。
# 本番では Secret 経由で実値が注入されるためフォールバックは使われない。
_configuration = Configuration(
    access_token=config.LINEBOT_CHANNEL_ACCESS_TOKEN or "dummy"
)
_api_client = ApiClient(_configuration)
line_bot_api = MessagingApi(_api_client)
line_bot_blob_api = MessagingApiBlob(_api_client)
handler = WebhookHandler(config.LINEBOT_CHANNEL_SECRET or "dummy")
