from flask import (
    request,
)
from typing import Dict, Tuple
from src.UseCases.Interface.IUseCase import IUseCase
from src.Infrastructure.Repositories import (
    stock_repository,
)
from src.models.StockViewModel import StockViewModel, keys, labels
from src.routes.Forms.AddStockForm import AddStockForm
from src.models.PageContents import PageContents


class ViewStockListUseCase(IUseCase):
    def execute(self, page_contents: PageContents) -> Tuple[Dict, AddStockForm]:
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
        page_contents.stocks = [StockViewModel(stock) for stock in stocks]
        page_contents.keys = keys
        page_contents.labels = labels

        form = AddStockForm(request.form)

        return page_contents, form
