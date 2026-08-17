import base64
import hashlib
import hmac
import time

from src import config

# 週次カレンダー画像URLの有効期限（14日）。
# 期限切れの古いリンクは 404 になり、画像を辿れなくなる。
TOKEN_TTL_SECONDS = 14 * 24 * 60 * 60


def _signing_key() -> bytes:
    return config.FLASK_SECRET_KEY.encode("utf-8")


def _sign(payload_b64: str) -> str:
    return hmac.new(_signing_key(), payload_b64.encode("ascii"), hashlib.sha256).hexdigest()


def generate_token(line_user_id: str, week_start_date: str, now: float | None = None) -> str:
    """line_user_id・対象週の開始日・有効期限を含む署名付きトークンを生成する。

    フォーマット: base64url(line_user_id|week_start_date|expires_at) + "." + hmac_sha256_hex
    """
    issued_at = int(now if now is not None else time.time())
    expires_at = issued_at + TOKEN_TTL_SECONDS
    payload = f"{line_user_id}|{week_start_date}|{expires_at}"
    payload_b64 = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")
    signature = _sign(payload_b64)
    return f"{payload_b64}.{signature}"


def verify_token(token: str, now: float | None = None) -> tuple[str, str] | None:
    """トークンを検証し、有効なら (line_user_id, week_start_date) を返す。

    署名不一致・期限切れ・不正な形式の場合は None を返す（呼び出し側は 404 として扱うこと）。
    """
    if not token or "." not in token:
        return None

    payload_b64, _, signature = token.partition(".")
    if not payload_b64 or not signature:
        return None

    expected_signature = _sign(payload_b64)
    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        padding = "=" * (-len(payload_b64) % 4)
        payload = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
        line_user_id, week_start_date, expires_at_str = payload.split("|")
        expires_at = int(expires_at_str)
    except (ValueError, UnicodeDecodeError):
        return None

    current_time = now if now is not None else time.time()
    if current_time > expires_at:
        return None

    return line_user_id, week_start_date
