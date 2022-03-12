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
from pymongo import DESCENDING


class ViewDeletedStockListUseCase(IUseCase):
    def execute(self) -> Tuple[Dict, AddStockForm]:
        page_contents = dict(session)
        page_contents['title'] = '削除済みストック一覧'

        web_user: WebUser = page_contents['login_user']
        stocks = stock_repository.find(
            query={
                '$and': [
                    {'$or': [
                        {'owner_id': web_user.linked_line_user_id},
                        {'owner_id': web_user._id},
                    ]},
                    {'status': 2},
                ],
            },
            sort=[
                ('updated_at', DESCENDING),
            ],
        )
        page_contents['stocks'] = [StockViewModel(stock) for stock in stocks]
        page_contents['keys'] = [
            'item_name',
            'str_created_at',
            'str_expiry_date',
        ]
        page_contents['labels'] = ['名前', '登録日', '期限']

        return page_contents
