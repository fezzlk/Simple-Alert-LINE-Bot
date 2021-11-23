from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_response_service,
)
from src.Infrastructure.Repositories import stock_repository


class ReplyStockUseCase(IUseCase):
    def execute(self) -> None:
        stocks = stock_repository.find()
        goods_name_list = [s.goods_name for s in stocks]
        line_response_service.add_message('食材一覧を表示します。')
        line_response_service.add_message('\n'.join(goods_name_list))
