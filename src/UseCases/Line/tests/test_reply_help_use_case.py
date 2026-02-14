from src.UseCases.Interface.ILineRequestService import ILineRequestService
from src.UseCases.Interface.ILineResponseService import ILineResponseService
from src.UseCases.Line.ReplyHelpUseCase import ReplyHelpUseCase


class DummyLineRequestService(ILineRequestService):
    def __init__(self, message: str):
        self._message = message
        self._event_type = "message"
        self._req_line_user_name = "dummy"
        self._req_line_user_id = "U1"
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


def test_reply_help_default_lists_commands():
    line_request_service = DummyLineRequestService(message="ヘルプ")
    line_response_service = DummyLineResponseService()
    use_case = ReplyHelpUseCase(
        line_request_service=line_request_service,
        line_response_service=line_response_service,
    )

    use_case.execute()

    assert any("使い方ガイド" in message for message in line_response_service.messages)
    assert any("一覧表示" in message for message in line_response_service.messages)


def test_reply_help_specific_keyword():
    line_request_service = DummyLineRequestService(message="ヘルプ 登録")
    line_response_service = DummyLineResponseService()
    use_case = ReplyHelpUseCase(
        line_request_service=line_request_service,
        line_response_service=line_response_service,
    )

    use_case.execute()

    assert any("期限が1週間前" in message for message in line_response_service.messages)
