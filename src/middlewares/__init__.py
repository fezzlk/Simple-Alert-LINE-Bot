from functools import wraps
from urllib.parse import quote
from flask import request, redirect, session
from src import config


def login_required(f):
    @wraps(f)
    def decorated_login_required(*args, **kwargs):
        # 認証を通っていない場合はログイン画面に遷移
        if 'login_user' not in session:
            # 相対パスのみ保持 → ドメインをまたがない
            next_path = request.path
            session['next_page_url'] = next_path
            return redirect(f'/line/login?next={quote(next_path, safe="")}')

        session.pop('next_page_url', None)
        return f(*args, **kwargs)

    return decorated_login_required
