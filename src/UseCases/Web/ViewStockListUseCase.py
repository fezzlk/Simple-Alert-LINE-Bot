from flask import (
    session,
    request,
)
from typing import Dict, Tuple
from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Interface.IUseCase import IUseCase
from src.Infrastructure.Repositories import (
    stock_repository,
)
from src.models.StockViewModel import StockViewModel
from src.routes.Forms.AddStockForm import AddStockForm


class ViewStockListUseCase(IUseCase):
    def execute(self) -> Tuple[Dict, AddStockForm]:
        page_contents = dict(session)
        page_contents['title'] = 'ストック一覧'

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
        page_contents['labels'] = ['名前', '期限', '登録日']

        form = AddStockForm(request.form)

        return page_contents, form