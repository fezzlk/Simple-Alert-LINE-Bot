from functools import wraps
from urllib.parse import quote
from flask import request, redirect, url_for, session
from src import config


def login_required(f):
    @wraps(f)
    def decorated_login_required(*args, **kwargs):
        print('call login required')

        # 認証を通っていない場合はログイン画面に遷移
        if 'login_user' not in session:
            next_path = request.full_path.rstrip('?')
            if config.SERVER_URL:
                next_url = f'{config.SERVER_URL.rstrip("/")}{next_path}'
            else:
                next_url = request.url
            session['next_page_url'] = next_url
            next_url = quote(next_url, safe='')
            return redirect(f'/line/login?next={next_url}')

        session.pop('next_page_url', None)
        return f(*args, **kwargs)

    return decorated_login_required


def set_message(f):
    @wraps(f)
    def decorated_set_message(*args, **kwargs):
        print('call set message')

        messages = [value for key, value in request.args.items()
                    if key == 'message']
        if len(messages) > 0:
            print(messages[0])
            session['message'] = messages[0]
        else:
            session['message'] = ''

        return f(*args, **kwargs)

    return decorated_set_message
