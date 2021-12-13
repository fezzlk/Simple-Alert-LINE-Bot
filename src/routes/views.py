from flask import Blueprint, request, render_template, url_for, redirect, session
from src.Domains.Entities.WebUser import WebUser
from src.oauth_client import oauth
from src.UseCases import view_weather_use_case, after_login_use_case
from src.middlewares import login_required

from src.Infrastructure.Repositories import (
    web_user_repository,
    line_user_repository,
)

views_blueprint = Blueprint('views_blueprint', __name__, url_prefix='/')

'''
Endpoints for Web
'''


@views_blueprint.route('/', methods=['GET'])
def index():
    page_contents = {'title': 'home'}
    if request.args.get('message') is not None:
        page_contents['message'] = request.args.get('message')
    else:
        page_contents['message'] = ''

    email = dict(session).get('login_email', '')
    page_contents['login_email'] = email
    login_name = dict(session).get('login_name', '')
    page_contents['login_name'] = login_name
    users = web_user_repository.find({'web_user_email': email})
    if len(users) == 0:
        new_web_user = WebUser(
            web_user_name=login_name,
            web_user_email=email,
        )
        user = web_user_repository.create(new_web_user)
    else:
        user = users[0]
    # 通知機能

    return render_template('pages/index.html', page_contents=page_contents)


@views_blueprint.route('/approve_line_account')
@login_required
def view_approve_line_account():
    email = dict(session).get('login_email', '')
    page_contents = {}
    page_contents['title'] = 'applove line account',
    page_contents['template_path'] = 'pages/line/approve.html',
    page_contents['login_email'] = email,

    web_users = web_user_repository.find({'web_user_email': email})

    line_users = line_user_repository.find(
        {'line_user_id': web_users[0].linked_line_user_id}
    )

    page_contents['line_user_name'] = line_users[0].line_user_name

    return render_template('pages/line/approve.html', page_contents=page_contents)


@views_blueprint.route('/line/approve', methods=['POST'])
def approve_line():
    web_user_repository.update(
        {'web_user_email': dict(session).get('login_email', '')},
        {'is_linked_line_user': True},
    )

    return redirect(url_for('views_blueprint.index'))


@ views_blueprint.route('/weather')
@ login_required
def view_weather():
    page_contents = view_weather_use_case.execute()
    return render_template('pages/weather/index.html', page_contents=page_contents)


'''
Auth
'''


@ views_blueprint.route('/login')
def login():
    email = dict(session).get('login_email', None)
    if email is not None:
        return redirect('/')

    google = oauth.create_client('google')
    redirect_uri = url_for('views_blueprint.authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@ views_blueprint.route('/authorize')
def authorize():
    result = after_login_use_case.execute()
    return redirect('/')


@ views_blueprint.route('/logout')
def logout():
    session.clear()
    return redirect('/')
