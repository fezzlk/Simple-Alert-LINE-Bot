import logging
from flask import (
    render_template,
    url_for,
    redirect,
    session,
    flash,
    request,
    abort,
)
from werkzeug.exceptions import BadRequest

from src.routes.web import views_blueprint
from src.models.PageContents import RegisterFormData
from src.UseCases.Web.ViewRegisterUseCase import ViewRegisterUseCase
from src.UseCases.Web.RegisterWebUserUseCase import RegisterWebUserUseCase
from src.UseCases.Web.RegisterLineUserUseCase import RegisterLineUserUseCase
from src.models.Forms.LocalLoginForm import LocalLoginForm
from src.models.Forms.RegisterWebUserForm import RegisterWebUserForm
from src.oauth_client import oauth
from src.Domains.Entities.WebUser import WebUser
from src import config
from src.Infrastructure.Repositories import web_user_repository
from src.services import web_user_service
from src.routes.web.helpers import flash_form_errors, build_page_contents, capture_next_url
from src import ui_messages


@views_blueprint.route('/register', methods=['GET'])
def view_register():
    page_contents = build_page_contents(session, request, RegisterFormData)
    page_contents, forms = ViewRegisterUseCase().execute(page_contents=page_contents)
    return render_template('pages/register.html', page_contents=page_contents, form=forms)


@views_blueprint.route('/register', methods=['POST'])
def register():
    page_contents = build_page_contents(session, request)
    try:
        web_user_name = RegisterWebUserUseCase(
            web_user_service=web_user_service,
        ).execute(page_contents=page_contents)
    except BadRequest:
        form = RegisterWebUserForm(request.form)
        flash_form_errors(form)
        return render_template('pages/register.html', page_contents=page_contents, form=form)
    # TODO: ユーザー画面作ったらユーザー画面に遷移するようにする
    redirect_to = session.pop('next_page_url', '/')
    flash(ui_messages.register_welcome(web_user_name), 'success')
    return redirect(redirect_to)


@views_blueprint.route('/login', methods=['GET', 'POST'])
@views_blueprint.route('/line/login', methods=['GET', 'POST'])
def login():
    capture_next_url(session, request)
    if config.IS_DEVELOPMENT and request.path == '/login':
        form = LocalLoginForm(request.form)
        if request.method == 'POST':
            if not form.validate():
                flash_form_errors(form)
                page_contents = build_page_contents(session, request)
                return render_template('pages/local_login.html', page_contents=page_contents, form=form)
            if not config.LOCAL_AUTH_USER_CODE or not config.LOCAL_AUTH_PASSWORD:
                flash('ローカルログインが設定されていません', 'danger')
            elif (
                form.user_code.data != config.LOCAL_AUTH_USER_CODE
                or form.password.data != config.LOCAL_AUTH_PASSWORD
            ):
                flash('ユーザーコードまたはパスワードが違います', 'danger')
            else:
                web_users = web_user_repository.find(
                    {'web_user_name': form.user_code.data}
                )
                if len(web_users) == 0:
                    new_web_user = WebUser(
                        web_user_name=form.user_code.data,
                        web_user_email=None,
                        linked_line_user_id=None,
                        is_linked_line_user=False,
                    )
                    web_user = web_user_repository.create(new_web_user=new_web_user)
                else:
                    web_user = web_users[0]
                session['login_user'] = {
                    '_id': str(web_user._id),
                    'web_user_name': web_user.web_user_name,
                    'web_user_email': web_user.web_user_email,
                    'linked_line_user_id': web_user.linked_line_user_id,
                    'is_linked_line_user': web_user.is_linked_line_user,
                }
                redirect_to = session.pop('next_page_url', '/')
                return redirect(redirect_to)
        page_contents = build_page_contents(session, request)
        return render_template('pages/local_login.html', page_contents=page_contents, form=form)

    if request.method != 'GET':
        abort(404)

    line = oauth.create_client('line')
    if config.SERVER_URL:
        redirect_uri = f'{config.SERVER_URL.rstrip("/")}/line/authorize'
    else:
        redirect_uri = url_for('views_blueprint.authorize', _external=True)
    return line.authorize_redirect(redirect_uri)


@views_blueprint.route('/authorize')
@views_blueprint.route('/line/authorize')
def authorize():
    line = oauth.create_client('line')
    token = line.authorize_access_token()
    profile = line.get('v2/profile', token=token).json()
    line_user_id = profile.get('userId')
    display_name = profile.get('displayName')

    session['login_line_user_id'] = line_user_id
    session['login_name'] = display_name
    session['access_token'] = token.get('access_token')
    session['id_token'] = token.get('id_token')

    web_users = web_user_repository.find(
        {'linked_line_user_id': line_user_id})

    if len(web_users) == 0:
        session['pending_line_user'] = {
            'line_user_id': line_user_id,
            'display_name': display_name,
        }
        return redirect(url_for('views_blueprint.line_register'))
    else:
        user = web_users[0]
        session['login_user'] = {
            '_id': str(user._id),
            'web_user_name': user.web_user_name,
            'web_user_email': user.web_user_email,
            'linked_line_user_id': user.linked_line_user_id,
            'is_linked_line_user': user.is_linked_line_user,
        }

    redirect_to = session.pop('next_page_url', '/')
    return redirect(redirect_to)


@views_blueprint.route('/logout')
def logout():
    session.clear()
    flash(ui_messages.logged_out(), 'success')
    return redirect(url_for('views_blueprint.index'))
