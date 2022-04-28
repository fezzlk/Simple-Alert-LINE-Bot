from flask import (
    request,
)
from typing import Tuple
from src.UseCases.Interface.IUseCase import IUseCase
from src.Infrastructure.Repositories import (
    stock_repository,
)
from src.models.StockViewModel import StockViewModel, keys, labels
from src.models.Forms.AddStockForm import AddStockForm
from src.models.PageContents import PageContents, StockListData


class ViewStockListUseCase(IUseCase):
    def execute(self, page_contents: PageContents[StockListData]) -> Tuple[PageContents[StockListData], AddStockForm]:
        page_contents.page_title = 'ストック一覧'

        web_user = page_contents.login_user
        stocks = stock_repository.find({
            '$and': [
                {'$or': [
                    {'owner_id': web_user.linked_line_user_id},
                    {'owner_id': web_user._id},
                ]},
                {'status': 1},
            ],
        })
        page_contents.data.stocks = [
            StockViewModel(stock=stock) for stock in stocks]
        page_contents.data.keys = keys
        page_contents.data.labels = labels

        form = AddStockForm(request.form)

        return page_contents, form
