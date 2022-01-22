from flask import (
    request,
    session,
)
from typing import Dict, Tuple
from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.Entities.Stock import Stock
from src.Domains.Entities.WebUser import WebUser
from werkzeug.exceptions import BadRequest
from datetime import datetime
from src.Infrastructure.Repositories import (
    stock_repository,
)
from src.routes.Forms.AddStockForm import AddStockForm


class AddStockUseCase(IUseCase):
    def execute(self) -> Tuple[Dict, AddStockForm]:
        form = AddStockForm(request.form)

        if not form.validate():
            raise BadRequest(
                ', '.join([f'{k}: {v}' for k, v in form.errors.items()]))

        page_contents = dict(session)
        web_user: WebUser = page_contents['login_user']

        item_name = form.item_name.data
        str_expiry_date = form.expiry_date.data

        expiry_date = datetime.strptime(
            str_expiry_date, '%Y-%m-%d'
        ) if str_expiry_date is not None else None

        new_stock = Stock(
            item_name=item_name,
            expiry_date=expiry_date,
            owner_id=web_user._id,
            status=1,
        )

        result = stock_repository.create(new_stock=new_stock)
        return result.item_name
