from flask import (
    request,
)
from typing import Tuple
from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.models.StockViewModel import StockViewModel, keys, labels
from src.models.Forms.AddStockForm import AddStockForm
from src.models.PageContents import PageContents, StockListData


class ViewStockListUseCase(IUseCase):
    def __init__(self, stock_repository: IStockRepository):
        self._stock_repository = stock_repository

    def execute(self, page_contents: PageContents[StockListData]) -> Tuple[PageContents[StockListData], AddStockForm]:
        page_contents.page_title = 'ストック一覧'

        web_user = page_contents.login_user
        stocks = self._stock_repository.find({
            'owner_id__in': [web_user.linked_line_user_id, web_user._id],
            'status': 1,
        })
        page_contents.data.stocks = [
            StockViewModel(stock=stock) for stock in stocks]
        page_contents.data.keys = keys
        page_contents.data.labels = labels

        form = AddStockForm(request.form)

        return page_contents, form
