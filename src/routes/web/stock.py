from flask import render_template, url_for, redirect, session, request, flash

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
from src.Infrastructure.Repositories import stock_repository
from src import ui_messages


@views_blueprint.route('/stock', methods=['GET'])
@login_required
def view_stock_list():
    page_contents = build_page_contents(session, request, StockListData)
    page_contents, forms = ViewStockListUseCase(
        stock_repository=stock_repository,
    ).execute(page_contents=page_contents)
    return render_template('pages/stock/index.html', page_contents=page_contents, form=forms)


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
    page_contents = build_page_contents(session, request)
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
