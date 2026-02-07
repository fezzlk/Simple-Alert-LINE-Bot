from functools import wraps
from flask import request, redirect, url_for, session


def login_required(f):
    @wraps(f)
    def decorated_login_required(*args, **kwargs):
        print('call login required')

        # 認証を通っていない場合はログイン画面に遷移
        if 'login_user' not in session:
            session['next_page_url'] = request.url
            return redirect(url_for('views_blueprint.login', next=request.url))

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
