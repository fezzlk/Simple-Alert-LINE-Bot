from datetime import datetime

from flask import flash, redirect, render_template, request, session, url_for

from src.routes.web import views_blueprint
from src.middlewares import login_required
from src.models.PageContents import StockListData
from src.routes.web.helpers import build_page_contents
from src.UseCases.Web.ViewStockListUseCase import ViewStockListUseCase
from src.UseCases.Web.AddStockUseCase import AddStockUseCase
from src.UseCases.Web.UpdateStockUseCase import UpdateStockUseCase
from src.UseCases.Web.DeleteStockUseCase import DeleteStockUseCase
from src.UseCases.Web.ViewDeletedStockListUseCase import ViewDeletedStockListUseCase
from src.UseCases.Web.CompleteDeleteStockUseCase import CompleteDeleteStockUseCase
from src.UseCases.Web.RestoreStockUseCase import RestoreStockUseCase
from src.Infrastructure.Repositories import (
    notification_schedule_repository,
    stock_repository,
)
from src import ui_messages


@views_blueprint.route('/stock', methods=['GET'])
@login_required
def view_stock_list():
    page_contents = build_page_contents(session, request, StockListData)
    page_contents, forms = ViewStockListUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    notify_time = "12:00"
    login_user = page_contents.login_user
    if login_user and login_user.linked_line_user_id:
        schedule = notification_schedule_repository.find_by_line_user_id(
            login_user.linked_line_user_id
        )
        if schedule and schedule.notify_time:
            notify_time = schedule.notify_time
    return render_template(
        'pages/stock/index.html',
        page_contents=page_contents,
        form=forms,
        notify_time=notify_time,
    )


@views_blueprint.route('/stock', methods=['POST'])
@login_required
def add_stock():
    page_contents = build_page_contents(session, request)
    item_name = AddStockUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    flash(ui_messages.stock_added(item_name), 'success')
    return redirect(url_for('views_blueprint.view_stock_list'))


@views_blueprint.route('/stock/update', methods=['POST'])
@login_required
def update_stock():
    page_contents = build_page_contents(session, request)
    UpdateStockUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    flash(ui_messages.stock_updated(), 'success')
    return redirect(url_for('views_blueprint.view_stock_list'))


@views_blueprint.route('/stock/delete', methods=['POST'])
@login_required
def delete_stock():
    page_contents = build_page_contents(session, request)
    DeleteStockUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    flash(ui_messages.stock_deleted(), 'success')
    return redirect(url_for('views_blueprint.view_stock_list'))


@views_blueprint.route('/stock/delete', methods=['GET'])
@login_required
def view_deleted_stock_list():
    page_contents = build_page_contents(session, request, StockListData)
    page_contents = ViewDeletedStockListUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    return render_template('pages/stock/trash.html', page_contents=page_contents)


@views_blueprint.route('/stock/complete_delete', methods=['POST'])
@login_required
def complete_delete_stock():
    page_contents = build_page_contents(session, request)
    CompleteDeleteStockUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    flash(ui_messages.stock_deleted_permanently(), 'success')
    return redirect(url_for('views_blueprint.view_deleted_stock_list'))


@views_blueprint.route('/stock/restore', methods=['POST'])
@login_required
def restore_stock():
    page_contents = build_page_contents(session, request)
    RestoreStockUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    flash(ui_messages.stock_restored(), 'success')
    return redirect(url_for('views_blueprint.view_deleted_stock_list'))


@views_blueprint.route('/stock/notify_schedule', methods=['POST'])
@login_required
def update_notify_schedule():
    page_contents = build_page_contents(session, request)
    login_user = page_contents.login_user
    if login_user is None or not login_user.linked_line_user_id:
        flash('LINE連携済みユーザーのみ通知時刻を設定できます。', 'danger')
        return redirect(url_for('views_blueprint.view_stock_list'))

    notify_time = (request.form.get('notify_time') or '').strip()
    try:
        datetime.strptime(notify_time, "%H:%M")
    except ValueError:
        flash('通知時刻は HH:MM 形式で入力してください。', 'danger')
        return redirect(url_for('views_blueprint.view_stock_list'))

    notification_schedule_repository.upsert(
        line_user_id=login_user.linked_line_user_id,
        notify_time=notify_time,
        timezone_name='Asia/Tokyo',
    )
    flash(f'通知時刻を {notify_time} に更新しました。', 'success')
    return redirect(url_for('views_blueprint.view_stock_list'))
