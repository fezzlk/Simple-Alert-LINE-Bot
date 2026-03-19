import hmac
from functools import wraps

from flask import abort, request

from src import config


def internal_api_auth_required(f):
    """Cloud Scheduler 等の内部 API 呼び出しを API キーで認証するデコレータ。

    リクエストヘッダー ``X-API-Key`` の値を ``INTERNAL_API_KEY`` 環境変数と
    タイミングセーフに比較する。開発環境 (IS_DEVELOPMENT) では認証をスキップする。
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if config.IS_DEVELOPMENT:
            return f(*args, **kwargs)

        if not config.INTERNAL_API_KEY:
            abort(503, description='INTERNAL_API_KEY is not configured.')

        provided_key = request.headers.get('X-API-Key', '')
        if not hmac.compare_digest(provided_key, config.INTERNAL_API_KEY):
            abort(401, description='Invalid or missing API key.')

        return f(*args, **kwargs)

    return decorated
