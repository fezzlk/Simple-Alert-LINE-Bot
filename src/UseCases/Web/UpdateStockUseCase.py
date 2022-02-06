from datetime import datetime
from hashlib import new
from flask import (
    request,
    session,
)
from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Interface.IUseCase import IUseCase
from werkzeug.exceptions import BadRequest
from src.Infrastructure.Repositories import (
    stock_repository,
)
from bson.objectid import ObjectId


class UpdateStockUseCase(IUseCase):
    def execute(self) -> None:
        form = request.form
        owner_web: WebUser = session.get('login_user')
        owner_line_id = owner_web.linked_line_user_id if owner_web.is_linked_line_user else ''

        stock_id = request.form.get('stock_id', None)
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
                    new_values[key] = datetime.strptime(val, '%Y-%m-%d')
                else:
                    new_values[key] = None

            elif key == 'str_created_at':
                if val == '':
                    raise BadRequest("日付は必須です。")
                new_values[key] = datetime.strptime(val, '%Y-%m-%d')

        print(stock_id)
        print(new_values)
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

        print(res)
