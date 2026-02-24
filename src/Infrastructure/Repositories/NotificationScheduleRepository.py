from datetime import datetime, timedelta, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo

from google.cloud import firestore

from src.Domains.Entities.NotificationSchedule import NotificationSchedule
from src.firestore_client import firestore_client


class NotificationScheduleRepository:
    _collection_name = "notification_schedules"
    _default_notify_time = "12:00"
    _default_timezone = "Asia/Tokyo"

    def _collection(self):
        return firestore_client.collection(self._collection_name)

    def find_due(self, now_utc: datetime, limit: int = 500) -> List[NotificationSchedule]:
        query = (
            self._collection()
            .where("enabled", "==", True)
            .where("next_notify_at", "<=", now_utc)
            .order_by("next_notify_at", direction=firestore.Query.ASCENDING)
            .limit(limit)
        )
        schedules: List[NotificationSchedule] = []
        for doc in query.stream():
            data = doc.to_dict() or {}
            data["line_user_id"] = doc.id
            schedules.append(NotificationSchedule(**data))
        return schedules

    def find_by_line_user_id(self, line_user_id: str) -> Optional[NotificationSchedule]:
        snapshot = self._collection().document(line_user_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        data["line_user_id"] = snapshot.id
        return NotificationSchedule(**data)

    def compute_next_notify_at(
        self,
        notify_time: Optional[str],
        timezone_name: Optional[str],
        base_time_utc: datetime,
    ) -> datetime:
        safe_notify_time = notify_time or self._default_notify_time
        safe_timezone = timezone_name or self._default_timezone
        try:
            hour, minute = [int(x) for x in safe_notify_time.split(":", 1)]
        except (ValueError, TypeError):
            hour, minute = [int(x) for x in self._default_notify_time.split(":", 1)]

        local_tz = ZoneInfo(safe_timezone)
        local_now = base_time_utc.astimezone(local_tz)
        try:
            next_local = local_now.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
            )
        except ValueError:
            default_hour, default_minute = [int(x) for x in self._default_notify_time.split(":", 1)]
            next_local = local_now.replace(
                hour=default_hour,
                minute=default_minute,
                second=0,
                microsecond=0,
            )
        if next_local <= local_now:
            next_local += timedelta(days=1)
        return next_local.astimezone(timezone.utc)

    def claim_and_schedule_next(self, line_user_id: str, now_utc: datetime) -> bool:
        doc_ref = self._collection().document(line_user_id)
        transaction = firestore_client.transaction()

        @firestore.transactional
        def _claim(tx):
            snapshot = doc_ref.get(transaction=tx)
            if not snapshot.exists:
                return False

            data = snapshot.to_dict() or {}
            if not data.get("enabled", True):
                return False

            next_notify_at = data.get("next_notify_at")
            if next_notify_at is None:
                return False
            if next_notify_at > now_utc:
                return False

            next_at = self.compute_next_notify_at(
                notify_time=data.get("notify_time"),
                timezone_name=data.get("timezone"),
                base_time_utc=now_utc,
            )
            tx.update(
                doc_ref,
                {
                    "next_notify_at": next_at,
                    "updated_at": now_utc,
                },
            )
            return True

        return bool(_claim(transaction))

    def upsert(
        self,
        line_user_id: str,
        notify_time: str = "12:00",
        timezone_name: str = "Asia/Tokyo",
        enabled: Optional[bool] = None,
        base_time_utc: Optional[datetime] = None,
    ) -> NotificationSchedule:
        now_utc = base_time_utc or datetime.now(timezone.utc)
        next_notify_at = self.compute_next_notify_at(
            notify_time=notify_time,
            timezone_name=timezone_name,
            base_time_utc=now_utc,
        )
        doc_ref = self._collection().document(line_user_id)
        snapshot = doc_ref.get()
        data = snapshot.to_dict() or {}
        merged_enabled = data.get("enabled", True) if enabled is None else enabled
        created_at = data.get("created_at", now_utc)
        payload = {
            "notify_time": notify_time,
            "timezone": timezone_name,
            "enabled": merged_enabled,
            "next_notify_at": next_notify_at,
            "updated_at": now_utc,
        }
        if not snapshot.exists:
            payload["created_at"] = now_utc
        doc_ref.set(payload, merge=True)
        return NotificationSchedule(
            line_user_id=line_user_id,
            notify_time=notify_time,
            timezone=timezone_name,
            enabled=merged_enabled,
            next_notify_at=next_notify_at,
            created_at=created_at,
            updated_at=now_utc,
        )
