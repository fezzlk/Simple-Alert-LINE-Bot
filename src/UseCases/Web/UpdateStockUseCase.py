from datetime import datetime
from flask import (
    request,
)
from src.UseCases.Interface.IUseCase import IUseCase
from werkzeug.exceptions import BadRequest


class UpdateStockUseCase(IUseCase):
    def execute(self) -> None:
        form = request.form
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

        print(new_values)
