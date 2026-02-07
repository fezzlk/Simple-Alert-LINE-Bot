from datetime import datetime

from src.Domains.Entities.Stock import Stock
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.UseCases.Line.AddStockUseCase import AddStockUseCase
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService


class DummyLineRequestService(ILineRequestService):
    def __init__(self, message: str, req_line_user_id: str = "U1"):
        self._message = message
        self._event_type = "message"
        self._req_line_user_name = "dummy"
        self._req_line_user_id = req_line_user_id
        self._req_line_group_id = None

    @property
    def message(self) -> str:
        return self._message

    @property
    def event_type(self) -> str:
        return self._event_type

    @property
    def req_line_user_name(self) -> str:
        return self._req_line_user_name

    @property
    def req_line_user_id(self) -> str:
        return self._req_line_user_id

    @property
    def req_line_group_id(self) -> str:
        return self._req_line_group_id

    def set_req_info(self, event) -> None:
        pass

    def delete_req_info(self) -> None:
        pass


class DummyLineResponseService(ILineResponseService):
    def __init__(self):
        self.messages = []

    def add_message(self, text: str) -> None:
        self.messages.append(text)

    def add_image(self, image_url: str) -> None:
        pass

    def reply(self, event) -> None:
        pass

    def push(self, to: str) -> None:
        pass

    def reset(self) -> None:
        pass

    def push_a_message(self, to: str, message: str) -> None:
        pass


class DummyStockRepository(IStockRepository):
    def __init__(self):
        self.created = None

    def create(self, new_stock: Stock) -> Stock:
        self.created = new_stock
        return new_stock

    def update(self, query, new_stock) -> int:
        return 0

    def delete(self, query) -> int:
        return 0

    def find(self, query) -> list[Stock]:
        return []


def test_add_stock_missing_item_name():
    line_request_service = DummyLineRequestService(message="登録")
    line_response_service = DummyLineResponseService()
    stock_repository = DummyStockRepository()
    use_case = AddStockUseCase(
        stock_repository=stock_repository,
        line_request_service=line_request_service,
        line_response_service=line_response_service,
    )

    use_case.execute()

    assert stock_repository.created is None
    assert len(line_response_service.messages) == 2


def test_add_stock_invalid_date_format():
    line_request_service = DummyLineRequestService(message="登録 milk 123456789")
    line_response_service = DummyLineResponseService()
    stock_repository = DummyStockRepository()
    use_case = AddStockUseCase(
        stock_repository=stock_repository,
        line_request_service=line_request_service,
        line_response_service=line_response_service,
    )

    use_case.execute()

    assert stock_repository.created is None
    assert len(line_response_service.messages) == 1


def test_add_stock_with_expiry_date():
    line_request_service = DummyLineRequestService(message="登録 milk 20250102")
    line_response_service = DummyLineResponseService()
    stock_repository = DummyStockRepository()
    use_case = AddStockUseCase(
        stock_repository=stock_repository,
        line_request_service=line_request_service,
        line_response_service=line_response_service,
    )

    use_case.execute()

    assert isinstance(stock_repository.created, Stock)
    assert stock_repository.created.item_name == "milk"
    assert stock_repository.created.expiry_date == datetime(2025, 1, 2)
    assert line_response_service.messages[-1].startswith('"milk"を期限')
