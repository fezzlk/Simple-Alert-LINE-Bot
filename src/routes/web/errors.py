import logging
from flask import render_template, session, request, flash
from werkzeug.exceptions import BadRequest, NotFound

from src.routes.web import views_blueprint
from src.routes.web.helpers import build_page_contents


@views_blueprint.errorhandler(Exception)
def handle_bad_request(e):
    logging.exception('Unhandled exception in request')
    page_contents = build_page_contents(session, request, None, 'サーバーエラー')
    flash('予期しないエラーが発生しました。時間をおいて再度お試しください。', 'danger')
    return render_template('pages/error.html', page_contents=page_contents), 500


@views_blueprint.errorhandler(BadRequest)
def handle_bad_request_status(e):
    page_contents = build_page_contents(session, request, None, '不正なリクエスト')
    flash('リクエストが正しくありません。入力内容をご確認ください。', 'warning')
    return render_template('pages/error.html', page_contents=page_contents), 400


@views_blueprint.errorhandler(NotFound)
def handle_not_found(e):
    page_contents = build_page_contents(session, request, None, 'ページが見つかりません')
    flash('お探しのページは見つかりませんでした。', 'warning')
    return render_template('pages/error.html', page_contents=page_contents), 404
