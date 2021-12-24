from datetime import datetime
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
        # [TODO] 4桁の場合年、2桁の場合年月に現在年月を適用する
        item_name = args[1] if len(args) >= 2 else None
        date_str = args[2] if len(args) >= 3 else None

        if item_name is None:
            line_response_service.add_message(
                '"食材登録 [食材名] [賞味期限YYMMDD]" と送ってください。')
            return

        expiry_date = None
        if date_str is not None:
            if len(date_str) != 6 and len(date_str) != 8:
                line_response_service.add_message(
                    '賞味期限のフォーマットは YYYYMMDD または YYMMDD')
                return

            if len(date_str) == 6:
                year = 2000 + int(date_str[:2])
            else:
                year = int(date_str[:4])
            month = int(date_str[-4:-2])
            day = int(date_str[-2:])
            expiry_date = datetime(year, month, day)

        new_stock = Stock(
            item_name=item_name,
            owner_id=line_request_service.req_line_user_id,
            expiry_date=expiry_date,
            status=1,
        )
        stock_repository.create(new_stock)
        line_response_service.add_message(f'"{item_name}"を登録しました')
