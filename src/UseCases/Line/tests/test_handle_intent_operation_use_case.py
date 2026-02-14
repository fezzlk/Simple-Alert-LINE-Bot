from src.Domains.Entities.Stock import Stock
from src.Domains.IRepositories.IStockRepository import IStockRepository
from src.UseCases.Line.HandleIntentOperationUseCase import HandleIntentOperationUseCase
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

    @message.setter
    def message(self, value: str) -> None:
        self._message = value

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
        self.buttons = []

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
        self.updated_query = None
        self.updated_values = None
        self.update_count = 1

    def create(self, new_stock: Stock) -> Stock:
        self.created = new_stock
        return new_stock

    def update(self, query, new_values) -> int:
        self.updated_query = query
        self.updated_values = new_values
        return self.update_count

    def delete(self, query) -> int:
        return 0

    def find(self, query=None) -> list[Stock]:
        return []


class DummyIntentParserService:
    def __init__(self, parsed):
        self.parsed = parsed

    def parse(self, message: str):
        return self.parsed


class DummyPendingOperationService:
    def __init__(self):
        self.store = {}

    def save(self, line_user_id: str, operation):
        self.store[line_user_id] = {"operation": operation}

    def get(self, line_user_id: str):
        return self.store.get(line_user_id)

    def clear(self, line_user_id: str):
        self.store.pop(line_user_id, None)


def test_register_requires_confirmation_then_execute():
    req = DummyLineRequestService(message="牛乳")
    res = DummyLineResponseService()
    repo = DummyStockRepository()
    parser = DummyIntentParserService(
        {"intent": "register", "item_name": "牛乳", "expiry_date": None}
    )
    pending = DummyPendingOperationService()
    use_case = HandleIntentOperationUseCase(
        stock_repository=repo,
        line_request_service=req,
        line_response_service=res,
        intent_parser_service=parser,
        pending_operation_service=pending,
    )

    use_case.execute()
    assert repo.created is None
    assert len(res.buttons) == 1

    req.message = "はい"
    use_case.execute()
    assert isinstance(repo.created, Stock)
    assert repo.created.item_name == "牛乳"


def test_delete_intent_updates_status():
    req = DummyLineRequestService(message="削除 牛乳")
    res = DummyLineResponseService()
    repo = DummyStockRepository()
    parser = DummyIntentParserService(
        {"intent": "delete", "item_name": "牛乳", "expiry_date": None}
    )
    pending = DummyPendingOperationService()
    use_case = HandleIntentOperationUseCase(
        stock_repository=repo,
        line_request_service=req,
        line_response_service=res,
        intent_parser_service=parser,
        pending_operation_service=pending,
    )

    use_case.execute()
    req.message = "はい"
    use_case.execute()

    assert repo.updated_query["item_name"] == "牛乳"
    assert repo.updated_values["status"] == 2


def test_register_with_expiry_date_executes_with_date():
    req = DummyLineRequestService(message="確定申告は3/15まで")
    res = DummyLineResponseService()
    repo = DummyStockRepository()
    parser = DummyIntentParserService(
        {"intent": "register", "item_name": "確定申告", "expiry_date": "2026-03-15"}
    )
    pending = DummyPendingOperationService()
    use_case = HandleIntentOperationUseCase(
        stock_repository=repo,
        line_request_service=req,
        line_response_service=res,
        intent_parser_service=parser,
        pending_operation_service=pending,
    )

    use_case.execute()
    req.message = "はい"
    use_case.execute()

    assert repo.created is not None
    assert repo.created.item_name == "確定申告"
    assert repo.created.expiry_date.strftime("%Y-%m-%d") == "2026-03-15"
