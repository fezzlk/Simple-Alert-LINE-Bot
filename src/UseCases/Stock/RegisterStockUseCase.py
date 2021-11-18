from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_response_service,
)


class RegisterStockUseCase(IUseCase):
    def execute() -> None:
        args = line_request_service.message.split()

        keyword = args[0]
        goods_name = args[1] if len(args) >= 2 else None
        period = args[2] if len(args) >= 3 else None
        line_response_service.add_message('在庫登録完了')
