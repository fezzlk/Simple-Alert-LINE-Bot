from functools import wraps
from flask import request, redirect, url_for, session
from src.Infrastructure.Repositories import web_user_repository


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print('call login required')

        # メールアドレスがわからない(認証を通っていない)場合はログイン画面に遷移
        if 'login_email' not in session:
            return redirect(url_for('views_blueprint.login', next=request.url))
        print('call login required2')

        web_users = web_user_repository.find(
            {'web_user_email': session['login_email']}
        )
        print('call login required3')

        # メールアドレスが一致する web user がいなければ新規作成画面に遷移
        if len(web_users) == 0:
            return redirect(url_for('views_blueprint.register', next=request.url))

        print('call login required4')
        # web user をログイン中ユーザーとしてセッションに保存し、通過
        user_dict = web_users[0].__dict__.copy()
        # bson.ObjectId は JSON 変換できないため
        user_dict['_id'] = str(user_dict['_id'])
        session['login_user'] = user_dict
        return f(*args, **kwargs)

    return decorated_function
