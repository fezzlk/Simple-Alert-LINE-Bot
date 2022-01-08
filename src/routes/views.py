from flask import (
    Blueprint,
    request,
    render_template,
    url_for,
    redirect,
    session,
    flash,
)
from src.Domains.Entities.Stock import Stock
from src.Domains.Entities.WebUser import WebUser
from src.oauth_client import oauth
from src.UseCases.Web.ViewWeatherUseCase import ViewWeatherUseCase
from src.middlewares import login_required, set_message
from datetime import datetime
from bson.objectid import ObjectId

from src.Infrastructure.Repositories import (
    web_user_repository,
    line_user_repository,
    stock_repository,
)
from src.services import web_user_service
from src.models.StockViewModel import StockViewModel
from werkzeug.exceptions import BadRequest, NotFound

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
    page_contents = dict(session)
    page_contents['title'] = 'ユーザー登録'
    return render_template('pages/register.html', page_contents=page_contents)


@views_blueprint.route('/register', methods=['POST'])
def register():
    web_user_email = request.form.get('web_user_email')
    web_user_name = request.form.get('web_user_name')
    if web_user_name == '':
        raise BadRequest('名前は必須項目です')

    if web_user_email == '':
        raise BadRequest('メールアドレスは必須項目です')

    new_web_user = WebUser(
        web_user_email=web_user_email,
        web_user_name=web_user_name,
    )
    web_user_service.find_or_create(new_web_user)

    # ユーザー画面作ったらユーザー画面に遷移するようにする
    return redirect(url_for('views_blueprint.index', message=f'Hi, {web_user_name}! Welcome to SALB!'))


@ views_blueprint.route('/line/approve', methods=['GET'])
@ login_required
@set_message
def view_approve_line_user():
    page_contents = dict(session)
    page_contents['title'] = 'LINEユーザー連携'

    web_user: WebUser = page_contents['login_user']
    line_users = line_user_repository.find(
        {'line_user_id': web_user.linked_line_user_id}
    )

    if len(line_users) != 0:
        page_contents['line_user_name'] = line_users[0].line_user_name

    return render_template(
        'pages/line/approve.html',
        page_contents=page_contents,
    )


@ views_blueprint.route('/line/approve', methods=['POST'])
def approve_line_user():
    page_contents = dict(session)
    web_user_repository.update(
        {'web_user_email': page_contents['login_email']},
        {'is_linked_line_user': True},
    )

    return redirect(url_for('views_blueprint.view_approve_line_user'))


@ views_blueprint.route('/stock', methods=['GET'])
@ login_required
@set_message
def view_stock_list():
    page_contents = dict(session)
    page_contents['title'] = '食材一覧'
    web_user: WebUser = page_contents['login_user']
    stocks = stock_repository.find({
        '$and': [
            {'$or': [
                {'owner_id': web_user.linked_line_user_id},
                {'owner_id': web_user._id},
            ]},
            {'status': 1},
        ],
    })
    page_contents['stocks'] = [StockViewModel(stock) for stock in stocks]
    page_contents['labels'] = ['名前', '賞味期限', '登録日']
    return render_template(
        'pages/stock/index.html',
        page_contents=page_contents,
    )


@ views_blueprint.route('/stock', methods=['POST'])
@ login_required
def create_stock():
    page_contents = dict(session)
    web_user: WebUser = page_contents['login_user']

    item_name = request.form.get('item_name', '')

    if item_name == '':
        raise BadRequest('アイテム名は必須です')

    str_expiry_date = request.form.get('expiry_date', '')

    expiry_date = datetime.strptime(
        str_expiry_date, '%Y-%m-%d'
    ) if str_expiry_date != '' else None

    new_stock = Stock(
        item_name=item_name,
        expiry_date=expiry_date,
        owner_id=web_user._id,
        status=1,
    )

    result = stock_repository.create(new_stock=new_stock)
    return redirect(url_for('views_blueprint.view_stock_list', message=f'"{result.item_name}" を追加しました'))


@ views_blueprint.route('/stock/delete', methods=['POST'])
@ login_required
@set_message
def delete_stock():
    stock_id = request.form.get('stock_id', '')
    if stock_id == '':
        raise BadRequest('アイテムIDは必須です')

    result = stock_repository.update(
        {'_id': ObjectId(stock_id)},
        {'status': 0},
    )
    if result == 0:
        raise NotFound('削除対象のアイテムが見つかりません')

    return redirect(url_for('views_blueprint.view_stock_list', message='アイテムを削除しました'))


@ views_blueprint.route('/weather', methods=['GET'])
@ login_required
@set_message
def view_weather():
    page_contents = dict(session)
    page_contents['title'] = '天気情報'
    page_contents = ViewWeatherUseCase().execute()
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
    return redirect(url_for('views_blueprint.index', message='ログアウトしました'))


'''
error handling
'''


@views_blueprint.errorhandler(Exception)
def handle_bad_request(e):
    page_contents = dict(session)
    page_contents['title'] = 'サーバーエラー'
    flash(e, 'danger')
    return render_template('pages/error.html', page_contents=page_contents)
