from flask import (
    request,
)
from typing import Tuple
from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.models.StockViewModel import StockViewModel, keys, labels
from src.models.Forms.AddStockForm import AddStockForm
from src.models.PageContents import PageContents, StockListData


class ViewStockListUseCase(IUseCase):
    _sortable_keys = {
        'item_name': 'item_name',
        'str_created_at': 'created_at',
        'str_expiry_date': 'expiry_date',
    }

    def __init__(self, stock_repository: IStockRepository):
        self._stock_repository = stock_repository

    def execute(self, page_contents: PageContents[StockListData]) -> Tuple[PageContents[StockListData], AddStockForm]:
        page_contents.page_title = 'ストック一覧'

        web_user = page_contents.login_user
        sort_key = request.args.get('sort_key', '')
        sort_order = request.args.get('sort_order', 'asc').lower()
        if sort_order not in ('asc', 'desc'):
            sort_order = 'asc'
        sort = None
        if sort_key in self._sortable_keys:
            sort = [(self._sortable_keys[sort_key], sort_order)]

        stocks = self._stock_repository.find(
            {
                'owner_id__in': [web_user.linked_line_user_id, web_user._id],
                'status': 1,
            },
            sort=sort,
        )
        page_contents.data.stocks = [
            StockViewModel(stock=stock) for stock in stocks]
        page_contents.data.keys = keys
        page_contents.data.labels = labels
        page_contents.data.sort_key = sort_key if sort_key in self._sortable_keys else ''
        page_contents.data.sort_order = sort_order if page_contents.data.sort_key else ''

        form = AddStockForm(request.form)

        return page_contents, form
