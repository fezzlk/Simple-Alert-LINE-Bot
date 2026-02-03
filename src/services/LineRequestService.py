from linebot.models.events import Event
from src.line_bot_api import line_bot_api
from src.UseCases.Interface.ILineRequestService import ILineRequestService


class LineRequestService(ILineRequestService):
    """LineRequestService
    メッセージ送信元の LINE ユーザー ID, トークルーム ID を管理
    """

    def __init__(self):
        # 受信メッセージ、送信元の LINE ユーザー ID, トークルーム ID, グループ ID
        self.message: str = None
        self.event_type: str = None
        self.message_type: str = None
        self.req_line_user_name: str = None
        self.req_line_user_id: str = None
        self.req_line_group_id: str = None

    @property
    def message(self) -> str:
        return self._message

    @message.setter
    def message(self, value: str) -> None:
        self._message = value

    @property
    def event_type(self) -> str:
        return self._event_type

    @event_type.setter
    def event_type(self, value: str) -> None:
        self._event_type = value

    @property
    def req_line_user_name(self) -> str:
        return self._req_line_user_name

    @req_line_user_name.setter
    def req_line_user_name(self, value: str) -> None:
        self._req_line_user_name = value

    @property
    def req_line_user_id(self) -> str:
        return self._req_line_user_id

    @req_line_user_id.setter
    def req_line_user_id(self, value: str) -> None:
        self._req_line_user_id = value

    @property
    def req_line_group_id(self) -> str:
        return self._req_line_group_id

    @req_line_group_id.setter
    def req_line_group_id(self, value: str) -> None:
        self._req_line_group_id = value

    """
    メッセージ送信元情報のセット
    """

    def set_req_info(self, event: Event) -> None:
        self.event_type = event.type
        if event.type == 'message':
            self.message_type = event.message.type
            if event.message.type == 'text':
                self.message = event.message.text

        self.req_line_user_id = event.source.user_id
        try:
            self.req_line_user_name = line_bot_api.get_profile(
                self.req_line_user_id
            ).display_name
        except BaseException:
            raise ValueError(
                f'Failed to get LINE profile "{self.req_line_user_id}"')

        if event.source.type == 'room':
            self.req_line_group_id = event.source.room_id
        if event.source.type == 'group':
            self.req_line_group_id = event.source.group_id

        print(
            f'Received message: "{self.message}" from {self.req_line_user_name}'
        )

    """
    メッセージ送信元情報の削除
    一つ前のメッセージ送信元の情報が残らないようにするために使う
    """

    def delete_req_info(self) -> None:
        self.event_type = None
        self.message = None
        self.req_line_user_name = None
        self.req_line_user_id = None
        self.req_line_group_id = None
