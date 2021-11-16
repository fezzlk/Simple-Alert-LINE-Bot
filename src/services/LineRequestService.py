from linebot.models.events import Event
from src.line_bot_api import line_bot_api


class LineRequestService:
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
        self.req_line_user_name = line_bot_api.get_profile(
            self.req_line_user_id
        ).display_name

        if event.source.type == 'room':
            self.req_line_group_id = event.source.room_id
        if event.source.type == 'group':
            self.req_line_group_id = event.source.group_id

        print(f"Received message: \"{self.message}\" from {self.user_name}")

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
