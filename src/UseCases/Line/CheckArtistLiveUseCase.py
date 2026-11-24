import logging
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from src.Domains.Entities.ArtistWatch import ConcertEvent
from src.services.ArtistLiveNotificationService import NotificationUnavailable

logger = logging.getLogger(__name__)
TOKYO = ZoneInfo("Asia/Tokyo")
UTC = timezone.utc


class CheckArtistLiveUseCase:
    """Process at most one artist per existing minute tick; scan once per JST day.

    This keeps network work under the existing Gunicorn timeout and avoids adding
    another Cloud Scheduler job. Failed sends retry from the durable outbox without
    re-running paid search requests. An unfinished scan is reclaimed after its lease.
    """
    def __init__(self, repository, web_user_repository, line_user_repository, source_service, notification_service):
        self.repository = repository
        self.web_users = web_user_repository
        self.line_users = line_user_repository
        self.sources = source_service
        self.notifications = notification_service

    def execute(self, now: datetime | None = None) -> dict:
        now = now or datetime.now(UTC)
        local_now = now.astimezone(TOKYO)
        day = local_now.date().isoformat()
        tomorrow = (local_now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        next_check = tomorrow.astimezone(UTC)
        for watch in self.repository.due_watches(now):
            claimed = self.repository.claim(watch._id, now)
            if not claimed:
                continue
            watch, token = claimed
            warnings = [warning for warning in watch.warnings if not warning.startswith("LINE")]
            if watch.last_scan_day != day:
                warnings = []
            status = "ok"
            scan_day = watch.last_scan_day
            checked_at = watch.last_checked_at
            try:
                owners = self.web_users.find({"_id": watch.owner_id})
                owner = owners[0] if owners else None
                target = owner.linked_line_user_id if owner and owner.is_linked_line_user else None
                if not target or not self.line_users.find({"line_user_id": target}):
                    status = "line_unlinked"
                    next_check = now + timedelta(hours=1)
                    warnings = ["LINE連携と友だち登録を確認してください。"]
                else:
                    if watch.last_scan_day != day:
                        discovery = self.sources.discover(
                            watch, local_now.date(), lambda: self.repository.reserve_search(now), time.monotonic() + 18
                        )
                        warnings = discovery.warnings
                        if not self.repository.current(watch._id, token):
                            return {"status": "watch_changed"}
                        for event in discovery.events:
                            self.repository.queue_event(watch, event, token)
                        scan_day = day
                        checked_at = now
                        if not discovery.checked_pages:
                            status = "error"
                            warnings.append("情報源を取得できず、新着の有無を確認できませんでした。")
                    if self.repository.current(watch._id, token):
                        pending = self.repository.pending_events(watch._id, watch.artist_name)
                        # One send per tick bounds HTTP work and allows other due watches to proceed.
                        if pending:
                            item = pending[0]
                            if ConcertEvent.from_dict(item["event"]).event_date >= local_now.date():
                                self.notifications.send(target, watch.artist_name, item)
                                self.repository.mark_sent(watch._id, item["_id"], item["fingerprint"])
                            else:
                                self.repository.discard_expired(watch._id, item["_id"])
                            if len(pending) > 1:
                                next_check = now + timedelta(minutes=1)
                if warnings and status == "ok":
                    status = "partial"
            except NotificationUnavailable as error:
                status = "notification_pending"
                warnings.append(str(error))
                next_check = now + timedelta(minutes=15)
            except Exception:
                # Tracebacks / HTTP exceptions may contain API keys. Store a safe, actionable status.
                logger.warning("Artist live check failed (%s)", watch._id)
                status = "error"
                warnings.append("チェックに失敗しました。時間をおいて再試行します。")
                next_check = now + timedelta(minutes=15)
            self.repository.finish(watch._id, token, next_check_at=next_check, last_scan_day=scan_day,
                                   last_checked_at=checked_at, status=status,
                                   warnings=list(dict.fromkeys(warnings)))
            return {"status": status, "processed": 1}
        return {"status": "idle", "processed": 0}
