from flask import (
    Blueprint,
    request,
    render_template,
    url_for,
    redirect,
    session,
)
from src.Domains.Entities.WebUser import WebUser
from src.oauth_client import oauth
from src.UseCases import view_weather_use_case
from src.middlewares import login_required

from src.Infrastructure.Repositories import (
    web_user_repository,
    line_user_repository,
)
from src.services import web_user_service

views_blueprint = Blueprint('views_blueprint', __name__, url_prefix='/')

'''
Endpoints for Web
'''


@views_blueprint.route('/', methods=['GET'])
def index():
    page_contents = dict(session)
    page_contents['title'] = 'Home'
    page_contents['message'] = request.args.get('message', '')

    return render_template('pages/index.html', page_contents=page_contents)


@views_blueprint.route('/register', methods=['GET'])
def view_register():
    page_contents = dict(session)
    page_contents['title'] = 'Register Web User'

    return render_template('pages/register.html', page_contents=page_contents)


@views_blueprint.route('/register', methods=['POST'])
def register():
    page_contents = dict(session)
    new_web_user = WebUser(
        web_user_email=page_contents['login_email'],
        web_user_name=page_contents['login_name'],
    )
    web_user_service.find_or_create()

    return redirect(url_for('views_blueprint.index'))  # ユーザー画面の方がいいかも


@views_blueprint.route('/line/approve', methods=['GET'])
@login_required
def view_approve_line_account():
    page_contents = dict(session)
    page_contents['title'] = 'Applove LINE Account',

    web_users = web_user_repository.find(
        {'web_user_email': page_contents['login_email']})

    line_users = line_user_repository.find(
        {'line_user_id': web_users[0].linked_line_user_id}
    )

    page_contents['line_user_name'] = line_users[0].line_user_name

    return render_template(
        'pages/line/approve.html',
        page_contents=page_contents,
    )


@views_blueprint.route('/line/approve', methods=['POST'])
def approve_line_account():
    page_contents = dict(session)
    web_user_repository.update(
        {'web_user_email': page_contents['login_email']},
        {'is_linked_line_user': True},
    )

    # return redirect(url_for('views_blueprint.index'))


@ views_blueprint.route('/weather')
@ login_required
def view_weather():
    page_contents = view_weather_use_case.execute()
    return render_template(
        'pages/weather/index.html',
        page_contents=page_contents,
    )


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
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    # do something with the token and profile
    email = user_info['email']
    user_name = user_info['name']
    session['login_email'] = email
    session['login_name'] = user_name
    session['login_picture'] = user_info['picture']
    session['access_token'] = token['access_token']
    session['id_token'] = token['id_token']

    web_users = web_user_repository.find(
        {'web_user_email': email})

    if len(web_users) == 0:
        return redirect('/register')

    return redirect('/')  # [TODO] 引数からリダイレクト先を指定する


@ views_blueprint.route('/logout')
def logout():
    session.clear()
    return redirect('/')
