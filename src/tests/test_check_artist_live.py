from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

from src.Domains.Entities.ArtistWatch import ArtistWatch, ConcertEvent
from src.services.ArtistLiveNotificationService import NotificationUnavailable
from src.services.ArtistLiveSourceService import DiscoveryResult
from src.UseCases.Line.CheckArtistLiveUseCase import CheckArtistLiveUseCase

NOW = datetime(2026, 11, 22, 0, tzinfo=timezone.utc)
EVENT = ConcertEvent("Chris Dave and friends", date(2027, 1, 8), "Billboard Live TOKYO", "https://example.com/show")


def build(watch=None):
    watch = watch or ArtistWatch("A1", "W1", "Chris Dave")
    repository = Mock()
    repository.due_watches.return_value = [watch]
    repository.claim.return_value = (watch, "lease")
    repository.current.return_value = True
    repository.pending_events.return_value = []
    sources = Mock()
    sources.discover.return_value = DiscoveryResult([EVENT], [], 3)
    notifications = Mock()
    owner = SimpleNamespace(_id="W1", linked_line_user_id="L1", is_linked_line_user=True)
    web_users = Mock()
    web_users.find.return_value = [owner]
    line_users = Mock()
    line_users.find.return_value = [SimpleNamespace()]
    return CheckArtistLiveUseCase(repository, web_users, line_users, sources, notifications)


def pending():
    return {"_id": "E1", "event": EVENT.to_dict(), "fingerprint": EVENT.fingerprint, "retry_key": "fixed-retry-key"}


def test_daily_scan_queues_new_events_and_uses_fresh_linked_recipient():
    case = build()
    case.repository.pending_events.return_value = [pending()]
    assert case.execute(NOW)["status"] == "ok"
    case.repository.queue_event.assert_called_once()
    case.notifications.send.assert_called_once_with("L1", "Chris Dave", pending())
    case.repository.mark_sent.assert_called_once_with("A1", "E1", EVENT.fingerprint)
    finished = case.repository.finish.call_args.kwargs
    assert finished["last_scan_day"] == "2026-11-22"
    assert finished["next_check_at"] == NOW + timedelta(days=1)


def test_retry_same_jst_day_sends_outbox_without_searching_again():
    case = build(ArtistWatch("A1", "W1", "Chris Dave", last_scan_day="2026-11-22", last_checked_at=NOW))
    case.repository.pending_events.return_value = [pending()]
    case.execute(NOW + timedelta(minutes=15))
    case.sources.discover.assert_not_called()
    case.notifications.send.assert_called_once()


def test_failed_notification_does_not_acknowledge_and_keeps_scan_day():
    case = build()
    case.repository.pending_events.return_value = [pending()]
    case.notifications.send.side_effect = NotificationUnavailable("LINE送信を再試行します")
    assert case.execute(NOW)["status"] == "notification_pending"
    case.repository.mark_sent.assert_not_called()
    finished = case.repository.finish.call_args.kwargs
    assert finished["last_scan_day"] == "2026-11-22"
    assert finished["next_check_at"] == NOW + timedelta(minutes=15)


def test_lost_claim_never_searches_or_sends():
    case = build()
    case.repository.claim.return_value = None
    assert case.execute(NOW)["processed"] == 0
    case.sources.discover.assert_not_called()
    case.notifications.send.assert_not_called()


def test_disabled_or_edited_while_fetching_cannot_send():
    case = build()
    case.repository.current.return_value = False
    assert case.execute(NOW)["status"] == "watch_changed"
    case.repository.queue_event.assert_not_called()
    case.notifications.send.assert_not_called()


def test_removed_line_link_never_uses_old_session_target_or_consumes_search():
    case = build()
    case.web_users.find.return_value = []
    assert case.execute(NOW)["status"] == "line_unlinked"
    case.sources.discover.assert_not_called()
    case.notifications.send.assert_not_called()


def test_all_sources_failing_is_not_reported_as_no_new_events():
    case = build()
    case.sources.discover.return_value = DiscoveryResult([], ["取得失敗"], 0)
    assert case.execute(NOW)["status"] == "error"
    case.notifications.send.assert_not_called()


def test_expired_outbox_is_discarded_without_recording_a_successful_send():
    case = build(ArtistWatch("A1", "W1", "Chris Dave", last_scan_day="2026-11-22"))
    item = pending()
    item["event"]["event_date"] = "2026-11-19"
    case.repository.pending_events.return_value = [item]
    case.execute(NOW)
    case.notifications.send.assert_not_called()
    case.repository.mark_sent.assert_not_called()
    case.repository.discard_expired.assert_called_once_with("A1", "E1")
