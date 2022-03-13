from flask import Request
from src.UseCases.Interface.IUseCase import IUseCase
from werkzeug.exceptions import BadRequest, NotFound
from src.Infrastructure.Repositories import (
    stock_repository,
)
from bson.objectid import ObjectId


class CompleteDeleteStockUseCase(IUseCase):
    def execute(self, page_contents: dict) -> None:
        request: Request = page_contents['request']
        stock_id = request.form.get('stock_id', '')
        if stock_id == '':
            raise BadRequest('アイテムIDは必須です')

        result = stock_repository.delete({
            '$and': [
                {'_id': ObjectId(stock_id)},
                {'status': 2},
            ],
        })
        if result == 0:
            raise NotFound('削除対象のアイテムが見つかりません')
