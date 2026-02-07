from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    session,
    flash,
    request,
)
from src.UseCases.Web.AddStockUseCase import AddStockUseCase
from src.UseCases.Web.ApproveLinkLineUserUseCase import ApproveLinkLineUserUseCase
from src.UseCases.Web.CompleteDeleteStockUseCase import CompleteDeleteStockUseCase
from src.UseCases.Web.DeleteStockUseCase import DeleteStockUseCase
from src.UseCases.Web.RegisterWebUserUseCase import RegisterWebUserUseCase
from src.UseCases.Web.RestoreStockUseCase import RestoreStockUseCase
from src.UseCases.Web.UpdateStockUseCase import UpdateStockUseCase
from src.UseCases.Web.ViewApproveLinkLineUseCase import ViewApproveLinkLineUseCase
from src.UseCases.Web.ViewDeletedStockListUseCase import ViewDeletedStockListUseCase
from src.UseCases.Web.ViewRegisterUseCase import ViewRegisterUseCase

from src.UseCases.Web.ViewStockListUseCase import ViewStockListUseCase
from src.UseCases.Web.RegisterLineUserUseCase import RegisterLineUserUseCase
from src.models.PageContents import PageContents, RegisterFormData, StockListData
from src.oauth_client import oauth
from src.middlewares import login_required, set_message
from src.Domains.Entities.WebUser import WebUser
from src.models.Forms.LineRegisterForm import LineRegisterForm
from src import config

from src.Infrastructure.Repositories import (
    web_user_repository,
    stock_repository,
    line_user_repository,
)
from src.services import web_user_service

views_blueprint = Blueprint('views_blueprint', __name__, url_prefix='/')


'''
Endpoints for Web
'''


@views_blueprint.route('/', methods=['GET'])
@set_message
def index():
    page_contents = PageContents(session, request)
    return render_template(
        'pages/index.html',
        page_contents=page_contents,
        line_add_friends_url=config.LINE_ADD_FRIENDS_URL,
        line_login_url=f'{config.SERVER_URL.rstrip("/")}/line/login' if config.SERVER_URL else '/line/login',
    )


@views_blueprint.route('/register', methods=['GET'])
@set_message
def view_register():
    page_contents = PageContents[RegisterFormData](
        session, request, RegisterFormData)
    page_contents, forms = ViewRegisterUseCase().execute(page_contents=page_contents)
    return render_template('pages/register.html', page_contents=page_contents, form=forms)


@views_blueprint.route('/register', methods=['POST'])
def register():
    page_contents = PageContents(session, request)
    web_user_name = RegisterWebUserUseCase(
        web_user_service=web_user_service,
    ).execute(page_contents=page_contents)
    # TODO: ユーザー画面作ったらユーザー画面に遷移するようにする
    redirect_to = session.pop('next_page_url', '/')
    return redirect(f'{redirect_to}?message=Hi, {web_user_name}! Welcome to SALB!')


@ views_blueprint.route('/line/approve', methods=['GET'])
@ login_required
@ set_message
def view_approve_link_line_user():
    page_contents = PageContents(session, request)
    page_contents = ViewApproveLinkLineUseCase(
        line_user_repository=line_user_repository,
    ).execute(page_contents=page_contents)
    return render_template('pages/line/approve.html', page_contents=page_contents)


@ views_blueprint.route('/line/approve', methods=['POST'])
def approve_line_user():
    page_contents = PageContents(session, request)
    ApproveLinkLineUserUseCase(
        web_user_repository=web_user_repository,
    ).execute(page_contents=page_contents)
    return redirect(url_for('views_blueprint.view_approve_link_line_user'))


@ views_blueprint.route('/stock', methods=['GET'])
@ login_required
@ set_message
def view_stock_list():
    page_contents = PageContents[StockListData](
        session, request, StockListData)
    page_contents, forms = ViewStockListUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    return render_template('pages/stock/index.html', page_contents=page_contents, form=forms)


@ views_blueprint.route('/stock', methods=['POST'])
@ login_required
def add_stock():
    page_contents = PageContents(session, request)
    item_name = AddStockUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    return redirect(url_for('views_blueprint.view_stock_list', message=f'"{item_name}" を追加しました'))


@ views_blueprint.route('/stock/update', methods=['POST'])
@ login_required
def update_stock():
    page_contents = PageContents(session, request)
    UpdateStockUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    return redirect(url_for('views_blueprint.view_stock_list', message=f'更新しました'))


@ views_blueprint.route('/stock/delete', methods=['POST'])
@ login_required
@ set_message
def delete_stock():
    page_contents = PageContents(session, request)
    DeleteStockUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    return redirect(url_for('views_blueprint.view_stock_list', message='アイテムを削除しました'))


@ views_blueprint.route('/stock/delete', methods=['GET'])
@ login_required
@ set_message
def view_deleted_stock_list():
    page_contents = PageContents(session, request)
    page_contents = ViewDeletedStockListUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    return render_template('pages/stock/trash.html', page_contents=page_contents)


@ views_blueprint.route('/stock/complete_delete', methods=['POST'])
@ login_required
def complete_delete_stock():
    page_contents = PageContents(session, request)
    CompleteDeleteStockUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    return redirect(url_for('views_blueprint.view_deleted_stock_list', message='アイテムを完全削除しました'))


@ views_blueprint.route('/stock/restore', methods=['POST'])
@ login_required
def restore_stock():
    page_contents = PageContents(session, request)
    RestoreStockUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    return redirect(url_for('views_blueprint.view_deleted_stock_list', message='アイテムを復元しました'))


'''
Auth
'''


@ views_blueprint.route('/login')
@ views_blueprint.route('/line/login')
def login():
    line = oauth.create_client('line')
    if config.SERVER_URL:
        redirect_uri = f'{config.SERVER_URL.rstrip("/")}/line/authorize'
    else:
        redirect_uri = url_for('views_blueprint.authorize', _external=True)
    return line.authorize_redirect(redirect_uri)


@ views_blueprint.route('/authorize')
@ views_blueprint.route('/line/authorize')
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


@ views_blueprint.route('/line/register', methods=['GET'])
def line_register():
    pending = session.get('pending_line_user')
    if not pending:
        return redirect(url_for('views_blueprint.login'))

    form = LineRegisterForm()
    form.web_user_name.data = pending.get('display_name') or ''
    page_contents = PageContents(session, request)
    return render_template('pages/line/register.html', form=form, page_contents=page_contents)


@ views_blueprint.route('/line/register', methods=['POST'])
def line_register_post():
    pending = session.get('pending_line_user')
    if not pending:
        return redirect(url_for('views_blueprint.login'))

    form = LineRegisterForm(request.form)
    if not form.validate():
        page_contents = PageContents(session, request)
        return render_template('pages/line/register.html', form=form, page_contents=page_contents)

    new_web_user = RegisterLineUserUseCase(
        web_user_repository=web_user_repository,
    ).execute(
        line_user_id=pending.get('line_user_id'),
        web_user_name=form.web_user_name.data,
    )
    session.pop('pending_line_user', None)
    session['login_user'] = {
        '_id': str(new_web_user._id),
        'web_user_name': new_web_user.web_user_name,
        'web_user_email': new_web_user.web_user_email,
        'linked_line_user_id': new_web_user.linked_line_user_id,
        'is_linked_line_user': new_web_user.is_linked_line_user,
    }

    redirect_to = session.pop('next_page_url', '/')
    return redirect(redirect_to)


@ views_blueprint.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('views_blueprint.index', message='ログアウトしました'))


'''
error handling
'''


@ views_blueprint.errorhandler(Exception)
def handle_bad_request(e):
    page_contents = PageContents(session, request, None, 'サーバーエラー')
    flash(e, 'danger')
    return render_template('pages/error.html', page_contents=page_contents)
