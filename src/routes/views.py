from flask import Blueprint, request, render_template, url_for, redirect, session
from src.oauth_client import oauth
from src.UseCases import view_weather_use_case, after_login_use_case
from src.middlewares import login_required

views_blueprint = Blueprint('views_blueprint', __name__, url_prefix='/')

'''
Endpoints for Web
'''


'''
Home
'''


@views_blueprint.route('/', methods=['GET'])
def index():
    page_contents = {'title': 'home'}
    if request.args.get('message') is not None:
        page_contents['message'] = request.args.get('message')
    else:
        page_contents['message'] = ''

    page_contents['login_email'] = dict(session).get('login_email', '')
    return render_template('pages/index.html', page_contents=page_contents)


'''
Auth
'''


@views_blueprint.route('/login')
def login():
    email = dict(session).get('login_email', None)
    if email is not None:
        return redirect('/')

    google = oauth.create_client('google')
    redirect_uri = url_for('views_blueprint.authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@views_blueprint.route('/authorize')
def authorize():
    after_login_use_case.execute()
    return redirect('/')


@views_blueprint.route('/logout')
def logout():
    session.clear()
    return redirect('/')


'''
contents
'''


@views_blueprint.route('/weather')
@login_required
def view_weather():
    page_contents = {'title': 'home'}
    page_contents['data'] = view_weather_use_case.execute()
    return render_template('pages/weather/index.html', page_contents=page_contents)
