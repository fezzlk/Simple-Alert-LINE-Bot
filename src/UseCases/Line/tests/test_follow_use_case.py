from src.Domains.Entities.LineUser import LineUser
from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService
from src.UseCases.Interface.ILineUserService import ILineUserService
from src.UseCases.Line.FollowUseCase import FollowUseCase


class DummyLineRequestService(ILineRequestService):
    def __init__(self, name: str, user_id: str):
        self._message = ""
        self._event_type = "follow"
        self._req_line_user_name = name
        self._req_line_user_id = user_id
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


class DummyLineUserService(ILineUserService):
    def __init__(self):
        self.created = None

    def find_or_create(self, new_line_user: LineUser) -> LineUser:
        self.created = new_line_user
        return new_line_user


class DummyNotificationScheduleRepository:
    def __init__(self):
        self.upserted_line_user_id = None

    def upsert(self, line_user_id: str, notify_time: str, timezone_name: str):
        self.upserted_line_user_id = line_user_id


def test_follow_use_case_creates_user_and_messages():
    request_service = DummyLineRequestService(name="Alice", user_id="U1")
    response_service = DummyLineResponseService()
    line_user_service = DummyLineUserService()
    notification_schedule_repository = DummyNotificationScheduleRepository()
    use_case = FollowUseCase(
        line_request_service=request_service,
        line_response_service=response_service,
        line_user_service=line_user_service,
        notification_schedule_repository=notification_schedule_repository,
    )

    use_case.execute()

    assert line_user_service.created is not None
    assert line_user_service.created.line_user_name == "Alice"
    assert line_user_service.created.line_user_id == "U1"
    assert notification_schedule_repository.upserted_line_user_id == "U1"
    assert any("友達登録ありがとうございます" in msg for msg in response_service.messages)
