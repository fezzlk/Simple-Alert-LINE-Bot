from flask import (
    request,
    session,
)
from typing import Dict, Tuple
from src.UseCases.Interface.IUseCase import IUseCase
from src.routes.Forms.RegisterWebUserForm import RegisterWebUserForm
from src.Domains.Entities.Stock import Stock
from src.Domains.Entities.WebUser import WebUser
from werkzeug.exceptions import BadRequest
from datetime import datetime
from src.Infrastructure.Repositories import (
    stock_repository,
)


class AddStockUseCase(IUseCase):
    def execute(self) -> Tuple[Dict, RegisterWebUserForm]:
        page_contents = dict(session)
        web_user: WebUser = page_contents['login_user']

        item_name = request.form.get('item_name', '')

        if item_name == '':
            raise BadRequest('アイテム名は必須です')

        str_expiry_date = request.form.get('expiry_date', '')

        expiry_date = datetime.strptime(
            str_expiry_date, '%Y-%m-%d'
        ) if str_expiry_date != '' else None

        new_stock = Stock(
            item_name=item_name,
            expiry_date=expiry_date,
            owner_id=web_user._id,
            status=1,
        )

        result = stock_repository.create(new_stock=new_stock)
