from src.Domains.Entities.Stock import Stock
from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_request_service,
    line_response_service,
)
from src.Infrastructure.Repositories import stock_repository


class RegisterStockUseCase(IUseCase):
    def execute(self) -> None:
        args = line_request_service.message.split()

        keyword = args[0]
        goods_name = args[1] if len(args) >= 2 else None
        period = args[2] if len(args) >= 3 else None
        print(f'register stock req: {goods_name} {period}')
        new_stock = Stock(
            goods_name=goods_name,
        )
        stock_repository.create(new_stock)
        line_response_service.add_message('食材を登録しました')
