from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository
from src.Domains.Entities.WebUser import WebUser
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService
from src.UseCases.Line.RequestLinkLineWebUseCase import RequestLinkLineWebUseCase


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


class DummyWebUserRepository(IWebUserRepository):
    def __init__(self, find_result: list = None):
        self._find_result = find_result or []

    def create(self, new_web_user: WebUser) -> WebUser:
        return new_web_user

    def update(self, query, new_web_user) -> int:
        return 0

    def delete(self, query) -> int:
        return 0

    def find(self, query) -> list:
        return self._find_result


def test_request_link_returns_deprecation_message():
    """アカウント連携機能は廃止済みのため、廃止メッセージとWebアプリURLを返す。"""
    response = DummyLineResponseService()
    use_case = RequestLinkLineWebUseCase(
        web_user_repository=DummyWebUserRepository(),
        line_request_service=DummyLineRequestService(message="アカウント連携"),
        line_response_service=response,
    )

    use_case.execute()

    assert len(response.messages) == 1
    assert "廃止" in response.messages[0]
    assert "LINEアカウント" in response.messages[0]
