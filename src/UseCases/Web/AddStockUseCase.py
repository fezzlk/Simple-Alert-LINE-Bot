from flask import (
    request,
    session,
)
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
    def execute(self) -> str:
        form = AddStockForm(request.form)
        form.expiry_date.data = form.expiry_date.raw_data[
            0] if form.expiry_date.raw_data[0] != '' else '0001-01-01'

        if not form.validate():
            raise BadRequest(
                ', '.join([f'{k}: {v}' for k, v in form.errors.items()]))

        page_contents = dict(session)
        web_user: WebUser = page_contents['login_user']

        item_name = form.item_name.data
        expiry_date = datetime.strptime(
            form.expiry_date.data, '%Y-%m-%d'
        ) if form.expiry_date.data != '0001-01-01' else None
        new_stock = Stock(
            item_name=item_name,
            expiry_date=expiry_date,
            owner_id=web_user._id,
            status=1,
        )

        result = stock_repository.create(new_stock=new_stock)
        return result.item_name
