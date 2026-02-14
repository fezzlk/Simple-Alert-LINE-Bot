from datetime import datetime
from src.Domains.Entities.Stock import Stock
from src.UseCases.Interface.IUseCase import IUseCase
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService


class AddStockUseCase(IUseCase):
    def __init__(
        self,
        stock_repository: IStockRepository,
        line_request_service: ILineRequestService,
        line_response_service: ILineResponseService,
    ):
        self._stock_repository = stock_repository
        self._line_request_service = line_request_service
        self._line_response_service = line_response_service

    def execute(self) -> None:
        message = (self._line_request_service.message or '').strip()
        item_name = None
        date_str = None

        if message.startswith('登録'):
            args = message.split()
            item_name = args[1] if len(args) >= 2 else None
            date_str = args[2] if len(args) >= 3 else None
        else:
            # Personal chat quick-add: plain text is treated as item name.
            item_name = message if message != '' else None

        if item_name is None:
            self._line_response_service.add_message(
                '"登録 [アイテム名] [期限(任意)]" と送ってください。')
            self._line_response_service.add_message(
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
                self._line_response_service.add_message(
                    '[日付の入力方法]\n\nYYYY年MM月DD日\n→ YYYYMMDD\n\n20YY年MM月DD日\n→ YYMMDD\n\n今年MM月DD日\n→ MMDD\n\n今月DD日\n→ DD')
                return

            expiry_date = datetime(year, month, day)

        new_stock = Stock(
            item_name=item_name,
            owner_id=self._line_request_service.req_line_user_id,
            expiry_date=expiry_date,
            status=1,
        )
        self._stock_repository.create(new_stock)

        if expiry_date is None:
            self._line_response_service.add_message(f'"{item_name}"を登録しました')
        else:
            self._line_response_service.add_message(
                f'"{item_name}"を期限{expiry_date.strftime("%Y年%m月%d日")}で登録しました')
