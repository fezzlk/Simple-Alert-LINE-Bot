from datetime import datetime
from src.Domains.Entities.Stock import Stock
from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    line_request_service,
    line_response_service,
)
from src.Infrastructure.Repositories import stock_repository


class AddStockUseCase(IUseCase):
    def execute(self) -> None:
        args = line_request_service.message.split()
        item_name = args[1] if len(args) >= 2 else None
        date_str = args[2] if len(args) >= 3 else None

        if item_name is None:
            line_response_service.add_message(
                '"登録 [アイテム名] [期限(任意)]" と送ってください。')
            line_response_service.add_message(
                '[日付の入力方法]\nYYYY年MM月DD日: YYYYMMDD\n20YY年MM月DD日: YYMMDD\n今年MM月DD日: MMDD\n今月DD日: DD')
            return

        expiry_date = None
        if date_str is not None:
            if len(date_str) % 2 == 1:
                date_str = '0' + date_str

            if len(date_str) == 8:
                year = int(date_str[:4])
                month = int(date_str[-4:-2])
                day = int(date_str[-2:])
            elif len(date_str) == 6:
                year = 2000 + int(date_str[:2])
                month = int(date_str[-4:-2])
                day = int(date_str[-2:])
            elif len(date_str) == 4:
                year = datetime.now().year
                month = int(date_str[-4:-2])
                day = int(date_str[-2:])
            elif len(date_str) == 2:
                year = datetime.now().year
                month = datetime.now().month
                day = int(date_str[-2:])
            else:
                line_response_service.add_message(
                    '[日付の入力方法]\n\nYYYY年MM月DD日\n→ YYYYMMDD\n\n20YY年MM月DD日\n→ YYMMDD\n\n今年MM月DD日\n→ MMDD\n\n今月DD日\n→ DD')
                return

            expiry_date = datetime(year, month, day)

        new_stock = Stock(
            item_name=item_name,
            owner_id=line_request_service.req_line_user_id,
            expiry_date=expiry_date,
            status=1,
        )
        stock_repository.create(new_stock)

        if expiry_date is None:
            line_response_service.add_message(f'"{item_name}"を登録しました')
        else:
            line_response_service.add_message(
                f'"{item_name}"を期限{expiry_date.strftime("%Y年%m月%d日")}で登録しました')
