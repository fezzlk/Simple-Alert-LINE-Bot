from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    session,
    flash,
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
from src.oauth_client import oauth
from src.UseCases.Web.ViewWeatherUseCase import ViewWeatherUseCase
from src.middlewares import login_required, set_message

from src.Infrastructure.Repositories import (
    web_user_repository,
    stock_repository,
)

views_blueprint = Blueprint('views_blueprint', __name__, url_prefix='/')


'''
Endpoints for Web
'''


@views_blueprint.route('/', methods=['GET'])
@set_message
def index():
    page_contents = dict(session)
    page_contents['title'] = 'ホーム'
    return render_template('pages/index.html', page_contents=page_contents)


@views_blueprint.route('/register', methods=['GET'])
@set_message
def view_register():
    page_contents, forms = ViewRegisterUseCase().execute()
    return render_template('pages/register.html', page_contents=page_contents, form=forms)


@views_blueprint.route('/register', methods=['POST'])
def register():
    web_user_name = RegisterWebUserUseCase().execute()
    # ユーザー画面作ったらユーザー画面に遷移するようにする
    redirect_to = session.pop('next', '/')
    return redirect(f'{redirect_to}?message=Hi, {web_user_name}! Welcome to SALB!')


@ views_blueprint.route('/line/approve', methods=['GET'])
@ login_required
@ set_message
def view_approve_link_line_user():
    page_contents = ViewApproveLinkLineUseCase().execute()
    return render_template('pages/line/approve.html', page_contents=page_contents)


@ views_blueprint.route('/line/approve', methods=['POST'])
def approve_line_user():
    ApproveLinkLineUserUseCase().execute()
    return redirect(url_for('views_blueprint.view_approve_link_line_user'))


@ views_blueprint.route('/stock', methods=['GET'])
@ login_required
@ set_message
def view_stock_list():
    page_contents, forms = ViewStockListUseCase().execute()
    return render_template('pages/stock/index.html', page_contents=page_contents, form=forms)


@ views_blueprint.route('/stock', methods=['POST'])
@ login_required
def add_stock():
    item_name = AddStockUseCase().execute()
    return redirect(url_for('views_blueprint.view_stock_list', message=f'"{item_name}" を追加しました'))


@ views_blueprint.route('/stock/update', methods=['POST'])
@ login_required
def update_stock():
    UpdateStockUseCase().execute()
    return redirect(url_for('views_blueprint.view_stock_list', message=f'更新しました'))


@ views_blueprint.route('/stock/delete', methods=['POST'])
@ login_required
@ set_message
def delete_stock():
    DeleteStockUseCase().execute()
    return redirect(url_for('views_blueprint.view_stock_list', message='アイテムを削除しました'))


@ views_blueprint.route('/stock/delete', methods=['GET'])
@ login_required
@ set_message
def view_deleted_stock_list():
    page_contents = ViewDeletedStockListUseCase().execute()
    return render_template('pages/stock/trash.html', page_contents=page_contents)


@ views_blueprint.route('/stock/complete_delete', methods=['POST'])
@ login_required
def complete_delete_stock():
    CompleteDeleteStockUseCase().execute()
    return redirect(url_for('views_blueprint.view_deleted_stock_list', message='アイテムを完全削除しました'))


@ views_blueprint.route('/stock/restore', methods=['POST'])
@ login_required
def restore_stock():
    RestoreStockUseCase().execute()
    return redirect(url_for('views_blueprint.view_deleted_stock_list', message='アイテムを復元しました'))


@ views_blueprint.route('/weather', methods=['GET'])
@ login_required
@ set_message
def view_weather():
    page_contents = ViewWeatherUseCase().execute()
    print(page_contents)
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

    redirect_to = session.pop('next', '/')

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
    page_contents = dict(session)
    page_contents['title'] = 'サーバーエラー'
    flash(e, 'danger')
    return render_template('pages/error.html', page_contents=page_contents)
