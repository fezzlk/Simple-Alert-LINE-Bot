from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage

from src import config
from src.Domains.Entities.ArtistWatch import ConcertEvent


class NotificationUnavailable(Exception):
    pass


class ArtistLiveNotificationService:
    def send(self, line_user_id: str, artist_name: str, pending: dict) -> None:
        if not config.LINEBOT_CHANNEL_ACCESS_TOKEN:
            raise NotificationUnavailable("LINE通知が未設定です。")
        # SDK v2 mutates its headers when retry_key is passed. Use a dedicated client
        # so the key cannot leak into unrelated stock / habit notifications.
        api = LineBotApi(config.LINEBOT_CHANNEL_ACCESS_TOKEN)
        quota = api.get_message_quota(timeout=2)
        consumption = api.get_message_quota_consumption(timeout=2)
        limit = min(getattr(quota, "value", 0) or 0, 190)
        if quota.type != "limited" or consumption.total_usage >= limit:
            raise NotificationUnavailable("LINEの月間通知上限に達したため送信を保留しています。")
        event = ConcertEvent.from_dict(pending["event"])
        if event.status == "cancelled":
            label = "公演中止"
        elif event.status == "postponed":
            label = "公演延期"
        else:
            label = "公演情報の更新" if pending.get("is_update") else "ライブ情報を発見"
        lines = [f"🎵 {label}", artist_name, event.title,
                 f"{event.event_date:%Y/%m/%d} · {event.venue}"]
        if event.ticket_info:
            lines.append(f"チケット発売情報: {event.ticket_info}")
        lines.append(event.source_url)
        try:
            api.push_message(line_user_id, TextSendMessage(text="\n".join(lines)[:4500]),
                             retry_key=pending["retry_key"], timeout=3)
        except LineBotApiError as error:
            # A retry of an accepted request is a successful delivery for our outbox.
            headers = {key.lower(): value for key, value in (error.headers or {}).items()}
            if error.status_code != 409 or not headers.get("x-line-accepted-request-id"):
                raise NotificationUnavailable("LINE送信に失敗したため再試行を待っています。") from None

