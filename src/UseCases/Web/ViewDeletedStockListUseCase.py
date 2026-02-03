from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.models.StockViewModel import StockViewModel, keys, labels
from src.models.PageContents import PageContents, StockListData
from pymongo import DESCENDING


class ViewDeletedStockListUseCase(IUseCase):
    def __init__(self, stock_repository: IStockRepository):
        self._stock_repository = stock_repository

    def execute(self, page_contents: PageContents[StockListData]) -> PageContents[StockListData]:
        page_contents.page_title = '削除済みストック一覧'
        web_user = page_contents.login_user
        stocks = self._stock_repository.find(
            query={
                '$and': [
                    {'$or': [
                        {'owner_id': web_user.linked_line_user_id},
                        {'owner_id': web_user._id},
                    ]},
                    {'status': 2},
                ],
            },
            sort=[
                ('updated_at', DESCENDING),
            ],
        )
        page_contents.data.stocks = [
            StockViewModel(stock=stock) for stock in stocks]
        page_contents.data.keys = keys
        page_contents.data.labels = labels

        return page_contents
