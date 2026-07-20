from src import config
from linebot import (LineBotApi, WebhookHandler)

# setup for line-bot-sdk
# トークン未設定（CI・テスト・.env 無しのローカル等）でも import 時に
# linebot SDK が None を連結して落ちないよう、ダミー値でフォールバックする。
# 本番では Secret 経由で実値が注入されるためフォールバックは使われない。
line_bot_api = LineBotApi(config.LINEBOT_CHANNEL_ACCESS_TOKEN or "dummy")
handler = WebhookHandler(config.LINEBOT_CHANNEL_SECRET or "dummy")
