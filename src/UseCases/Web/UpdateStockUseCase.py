from datetime import datetime

from flask import Request, request
from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Interface.IUseCase import IUseCase
from werkzeug.exceptions import BadRequest
from src.Infrastructure.Repositories import (
    stock_repository,
)
from bson.objectid import ObjectId
from src.models.PageContents import PageContents


class UpdateStockUseCase(IUseCase):
    def execute(self, page_contents: PageContents) -> None:
        request: Request = page_contents.request
        form = request.form
        owner_web: WebUser = page_contents.get('login_user')
        owner_line_id = owner_web.linked_line_user_id if owner_web.is_linked_line_user else ''

        stock_id = form.get('stock_id', None)
        if stock_id is None:
            raise BadRequest('stock_id が指定されていません。')
        new_values = {}

        for key in form:
            val = form.get(key)

            if key == 'item_name':
                if val == '':
                    raise BadRequest("名前は必須です。")
                new_values[key] = val

            elif key == 'str_expiry_date':
                if val != '':
                    new_values['expiry_date'] = datetime.strptime(
                        val, '%Y-%m-%d')
                else:
                    new_values['expiry_date'] = None

            elif key == 'str_created_at':
                if val == '':
                    raise BadRequest("日付は必須です。")
                new_values['created_at'] = datetime.strptime(val, '%Y-%m-%d')

        res = stock_repository.update(
            query={
                '$and': [
                    {'_id': ObjectId(stock_id)},
                    {'$or': [
                        {'owner_id': owner_web._id},
                        {'owner_id': owner_line_id},
                    ]}
                ]
            },
            new_values=new_values,
        )
