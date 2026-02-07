from src.Domains.Entities.WebUser import WebUser
from src.Domains.IRepositories.IWebUserRepository import IWebUserRepository
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
    def __init__(self, find_result: list[WebUser], update_result: int = 1):
        self._find_result = find_result
        self._update_result = update_result
        self.updated = None

    def create(self, new_web_user: WebUser) -> WebUser:
        return new_web_user

    def update(self, query, new_web_user) -> int:
        self.updated = (query, new_web_user)
        return self._update_result

    def delete(self, query) -> int:
        return 0

    def find(self, query) -> list[WebUser]:
        return self._find_result


def test_request_link_invalid_args():
    use_case = RequestLinkLineWebUseCase(
        web_user_repository=DummyWebUserRepository(find_result=[]),
        line_request_service=DummyLineRequestService(message="アカウント連携"),
        line_response_service=DummyLineResponseService(),
    )

    use_case.execute()

    assert any("アカウント連携" in message for message in use_case._line_response_service.messages)


def test_request_link_email_not_found():
    response = DummyLineResponseService()
    use_case = RequestLinkLineWebUseCase(
        web_user_repository=DummyWebUserRepository(find_result=[]),
        line_request_service=DummyLineRequestService(message="アカウント連携 test@example.com"),
        line_response_service=response,
    )

    use_case.execute()

    assert any("登録されていません" in message for message in response.messages)


def test_request_link_already_linked():
    response = DummyLineResponseService()
    web_user = WebUser(
        _id="507f1f77bcf86cd799439011",
        web_user_name="dummy",
        web_user_email="test@example.com",
        is_linked_line_user=True,
    )
    use_case = RequestLinkLineWebUseCase(
        web_user_repository=DummyWebUserRepository(find_result=[web_user]),
        line_request_service=DummyLineRequestService(message="アカウント連携 test@example.com"),
        line_response_service=response,
    )

    use_case.execute()

    assert any("すでに LINE アカウントと紐付けされています" in message for message in response.messages)


def test_request_link_update_failure():
    response = DummyLineResponseService()
    web_user = WebUser(
        _id="507f1f77bcf86cd799439011",
        web_user_name="dummy",
        web_user_email="test@example.com",
        is_linked_line_user=False,
    )
    use_case = RequestLinkLineWebUseCase(
        web_user_repository=DummyWebUserRepository(find_result=[web_user], update_result=0),
        line_request_service=DummyLineRequestService(message="アカウント連携 test@example.com"),
        line_response_service=response,
    )

    use_case.execute()

    assert any("失敗しました" in message for message in response.messages)


def test_request_link_success():
    response = DummyLineResponseService()
    web_user = WebUser(
        _id="507f1f77bcf86cd799439011",
        web_user_name="dummy",
        web_user_email="test@example.com",
        is_linked_line_user=False,
    )
    repo = DummyWebUserRepository(find_result=[web_user], update_result=1)
    use_case = RequestLinkLineWebUseCase(
        web_user_repository=repo,
        line_request_service=DummyLineRequestService(message="アカウント連携 test@example.com"),
        line_response_service=response,
    )

    use_case.execute()

    assert repo.updated is not None
    assert any("承認してください" in message for message in response.messages)
