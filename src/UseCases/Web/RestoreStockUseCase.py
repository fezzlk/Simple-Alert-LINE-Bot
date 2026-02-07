from flask import (
    Request,
)
from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.IRepositories.IStockRepository import IStockRepository
from werkzeug.exceptions import BadRequest, NotFound
from bson.objectid import ObjectId
from src.models.PageContents import PageContents


class RestoreStockUseCase(IUseCase):
    def __init__(self, stock_repository: IStockRepository):
        self._stock_repository = stock_repository

    def execute(self, page_contents: PageContents) -> str:
        request: Request = page_contents.request
        stock_id = request.form.get('stock_id', '')
        if stock_id == '':
            raise BadRequest('アイテムIDは必須です')

        result = self._stock_repository.update(
            {'$and': [
                {'_id': ObjectId(stock_id)},
                {'status': 2},
            ]},
            {'status': 1},
        )
        if result == 0:
            raise NotFound('復元対象のアイテムが見つかりません')
