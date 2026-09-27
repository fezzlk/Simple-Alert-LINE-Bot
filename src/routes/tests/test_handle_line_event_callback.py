import base64
import hashlib
import hmac
import json

import pytest
from linebot.v3.exceptions import InvalidSignatureError

from src.line_bot_api import handler

# LINE webhook のサンプル follow イベント。
# https://developers.line.biz/en/reference/messaging-api/#follow-event
_FOLLOW_EVENT_BODY = json.dumps({
    "destination": "xxxxxxxxxx",
    "events": [
        {
            "type": "follow",
            "mode": "active",
            "timestamp": 1462629479859,
            "source": {
                "type": "user",
                "userId": "U4af4980629L0000000000000000000",
            },
            "webhookEventId": "01FZ74A0TQ3TSPBI0000000000000",
            "deliveryContext": {"isRedelivery": False},
            "replyToken": "757913772c46000000000000000000",
            "follow": {"isUnblocked": False},
        },
    ],
})


def _sign(body: str) -> str:
    """テスト対象の channel secret で body に対する正しい署名を生成する。"""
    secret = handler.parser.signature_validator.channel_secret
    digest = hmac.new(secret, body.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def test_parser_accepts_valid_signature():
    """正しい署名の場合、v3 WebhookParser がイベントを解析できること。"""
    valid_signature = _sign(_FOLLOW_EVENT_BODY)

    events = handler.parser.parse(_FOLLOW_EVENT_BODY, valid_signature)

    assert len(events) == 1
    assert events[0].type == "follow"
    assert events[0].source.type == "user"
    assert events[0].source.user_id == "U4af4980629L0000000000000000000"


def test_parser_rejects_invalid_signature():
    """不正な署名の場合、v3 WebhookParser が InvalidSignatureError を送出すること。"""
    with pytest.raises(InvalidSignatureError):
        handler.parser.parse(_FOLLOW_EVENT_BODY, "invalid-signature==")


def test_callback_route_returns_400_for_invalid_signature(dummy_app):
    """署名検証に失敗した場合、/callback が 400 を返すこと（ユースケース実行前に abort される）。"""
    client = dummy_app.test_client()

    response = client.post(
        "/callback",
        data=_FOLLOW_EVENT_BODY,
        headers={"X-Line-Signature": "invalid-signature=="},
    )

    assert response.status_code == 400
