from flask import Request
from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.Entities.Stock import Stock
from src.Domains.IRepositories.IStockRepository import IStockRepository
from werkzeug.exceptions import BadRequest
from datetime import datetime
from src.models.Forms.AddStockForm import AddStockForm
from src.models.PageContents import PageContents


class AddStockUseCase(IUseCase):
    def __init__(self, stock_repository: IStockRepository):
        self._stock_repository = stock_repository

    def execute(self, page_contents: PageContents) -> str:
        request: Request = page_contents.request
        form = AddStockForm(request.form)
        form.expiry_date.data = form.expiry_date.raw_data[
            0] if form.expiry_date.raw_data[0] != '' else '0001-01-01'

        if not form.validate():
            raise BadRequest(
                ', '.join([f'{k}: {v}' for k, v in form.errors.items()]))

        web_user = page_contents.login_user

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

        result = self._stock_repository.create(new_stock=new_stock)
        return result.item_name
