from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.models.StockViewModel import StockViewModel, keys, labels
from src.models.PageContents import PageContents, StockListData


class ViewDeletedStockListUseCase(IUseCase):
    def __init__(self, stock_repository: IStockRepository):
        self._stock_repository = stock_repository

    def execute(self, page_contents: PageContents[StockListData]) -> PageContents[StockListData]:
        page_contents.page_title = '削除済みストック一覧'
        web_user = page_contents.login_user
        stocks = self._stock_repository.find(
            query={
                'owner_id__in': [web_user.linked_line_user_id, web_user._id],
                'status': 2,
            },
            sort=[
                ('updated_at', 'desc'),
            ],
        )
        page_contents.data.stocks = [
            StockViewModel(stock=stock) for stock in stocks]
        page_contents.data.keys = keys
        page_contents.data.labels = labels

        return page_contents
