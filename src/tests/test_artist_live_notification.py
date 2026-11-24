from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from linebot.exceptions import LineBotApiError

from src import config
from src.services import ArtistLiveNotificationService as notification_module
from src.tests.test_check_artist_live import pending


@pytest.fixture
def sender(monkeypatch):
    api = Mock()
    api.get_message_quota.return_value = SimpleNamespace(type="limited", value=200)
    api.get_message_quota_consumption.return_value = SimpleNamespace(total_usage=12)
    monkeypatch.setattr(config, "LINEBOT_CHANNEL_ACCESS_TOKEN", "test-token")
    monkeypatch.setattr(notification_module, "LineBotApi", lambda _: api)
    return notification_module.ArtistLiveNotificationService(), api


def test_push_contains_source_and_reuses_persisted_retry_key(sender):
    service, api = sender
    service.send("L1", "Chris Dave", pending())
    args, kwargs = api.push_message.call_args
    assert args[0] == "L1"
    assert "2027/01/08" in args[1].text
    assert "https://example.com/show" in args[1].text
    assert kwargs["retry_key"] == "fixed-retry-key"


def test_artist_notifications_stop_with_reserve_for_existing_reminders(sender):
    service, api = sender
    api.get_message_quota_consumption.return_value = SimpleNamespace(total_usage=190)
    with pytest.raises(notification_module.NotificationUnavailable, match="上限"):
        service.send("L1", "Chris Dave", pending())
    api.push_message.assert_not_called()


def test_line_retry_already_accepted_is_acknowledged(sender):
    service, api = sender
    api.push_message.side_effect = LineBotApiError(status_code=409, headers={"x-line-accepted-request-id": "accepted"},
                                                 error=SimpleNamespace(message="conflict"))
    service.send("L1", "Chris Dave", pending())


def test_unaccepted_line_conflict_is_not_acknowledged(sender):
    service, api = sender
    api.push_message.side_effect = LineBotApiError(status_code=409, headers={}, error=SimpleNamespace(message="conflict"))
    with pytest.raises(notification_module.NotificationUnavailable, match="再試行"):
        service.send("L1", "Chris Dave", pending())
