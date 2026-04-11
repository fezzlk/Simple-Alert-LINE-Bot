from functools import wraps
from urllib.parse import quote
from flask import request, redirect, session
from src import config


def login_required(f):
    @wraps(f)
    def decorated_login_required(*args, **kwargs):
        # 認証を通っていない場合はログイン画面に遷移
        if 'login_user' not in session:
            # openExternalBrowser 等の不要なパラメータを除いてパスのみ保持
            # → OAuth 後のリダイレクト先でブラウザ切り替えが起きないようにする
            next_path = request.path
            if config.SERVER_URL:
                next_url = f'{config.SERVER_URL.rstrip("/")}{next_path}'
            else:
                next_url = request.url_root.rstrip('/') + next_path
            session['next_page_url'] = next_url
            next_url = quote(next_url, safe='')
            return redirect(f'/line/login?next={next_url}')

        session.pop('next_page_url', None)
        return f(*args, **kwargs)

    return decorated_login_required
