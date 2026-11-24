from datetime import datetime, timedelta, timezone
from uuid import uuid4

from google.cloud import firestore

from src.Domains.Entities.ArtistWatch import ArtistWatch, ConcertEvent
from src.firestore_client import firestore_client

# This is an application-wide allowance, shared by all watches and concurrent workers.
# Keep a reserve below Brave Search's 1,000 requests / month credit allowance.
MONTHLY_SEARCH_LIMIT = 900
UTC = timezone.utc


class ArtistWatchRepository:
    def _collection(self):
        return firestore_client.collection("artist_watches")

    def list_for_owner(self, owner_id: str) -> list[ArtistWatch]:
        documents = self._collection().where("owner_id", "==", owner_id).stream()
        return sorted(
            [ArtistWatch.from_document(doc.id, doc.to_dict()) for doc in documents],
            key=lambda watch: (not watch.enabled, watch.artist_name.casefold()),
        )

    def save(self, owner_id: str, artist_name: str, aliases: list, source_urls: list,
             watch_id: str = "") -> str:
        now = datetime.now(UTC)
        ref = self._collection().document(watch_id) if watch_id else self._collection().document()

        @firestore.transactional
        def save_watch(tx):
            snapshot = ref.get(transaction=tx)
            existing = snapshot.to_dict() or {}
            if watch_id and (not snapshot.exists or existing.get("owner_id") != owner_id):
                raise LookupError("Watch not found")
            data = {"owner_id": owner_id, "artist_name": artist_name, "aliases": aliases,
                    "source_urls": source_urls, "updated_at": now, "next_check_at": now}
            if not snapshot.exists:
                data.update(enabled=True, status="waiting", created_at=now)
            elif any(existing.get(key) != data[key] for key in ("artist_name", "aliases", "source_urls")):
                # Editing the watch intentionally requests a fresh check.
                data.update(last_scan_day="", status="waiting", lease_token="", lease_until=None)
            tx.set(ref, data, merge=True)

        save_watch(firestore_client.transaction())
        return ref.id

    def set_enabled(self, owner_id: str, watch_id: str, enabled: bool) -> None:
        ref = self._collection().document(watch_id)

        @firestore.transactional
        def update(tx):
            snapshot = ref.get(transaction=tx)
            if not snapshot.exists or snapshot.to_dict().get("owner_id") != owner_id:
                raise LookupError("Watch not found")
            tx.update(ref, {"enabled": enabled, "next_check_at": datetime.now(UTC),
                            "lease_token": "", "lease_until": None})

        update(firestore_client.transaction())

    def due_watches(self, now: datetime) -> list[ArtistWatch]:
        # A single-field query avoids a new Firestore composite index / deployment requirement.
        watches = [ArtistWatch.from_document(doc.id, doc.to_dict())
                   for doc in self._collection().where("enabled", "==", True).stream()]
        watches = [watch for watch in watches if not watch.next_check_at or watch.next_check_at <= now]
        return sorted(watches, key=lambda watch: watch.next_check_at or datetime.min.replace(tzinfo=UTC))

    def claim(self, watch_id: str, now: datetime) -> tuple[ArtistWatch, str] | None:
        ref = self._collection().document(watch_id)
        token = str(uuid4())

        @firestore.transactional
        def claim_watch(tx):
            snapshot = ref.get(transaction=tx)
            data = snapshot.to_dict() or {}
            if not snapshot.exists or not data.get("enabled"):
                return None
            if data.get("next_check_at") and data["next_check_at"] > now:
                return None
            if data.get("lease_until") and data["lease_until"] > now:
                return None
            tx.update(ref, {"lease_token": token, "lease_until": now + timedelta(seconds=55)})
            return ArtistWatch.from_document(watch_id, data), token

        return claim_watch(firestore_client.transaction())

    def current(self, watch_id: str, token: str) -> bool:
        snapshot = self._collection().document(watch_id).get()
        data = snapshot.to_dict() or {}
        return bool(snapshot.exists and data.get("enabled") and data.get("lease_token") == token)

    def finish(self, watch_id: str, token: str, **values) -> None:
        ref = self._collection().document(watch_id)

        @firestore.transactional
        def finish_watch(tx):
            snapshot = ref.get(transaction=tx)
            if snapshot.exists and snapshot.to_dict().get("lease_token") == token:
                tx.update(ref, {**values, "lease_token": "", "lease_until": None})

        finish_watch(firestore_client.transaction())

    def reserve_search(self, now: datetime) -> bool:
        # Reserve BEFORE issuing HTTP, including failed calls. Transactions serialize concurrent calls.
        ref = firestore_client.collection("artist_watch_usage").document(now.strftime("%Y-%m"))

        @firestore.transactional
        def reserve(tx):
            snapshot = ref.get(transaction=tx)
            used = (snapshot.to_dict() or {}).get("requests", 0)
            if used >= MONTHLY_SEARCH_LIMIT:
                return False
            tx.set(ref, {"requests": used + 1, "updated_at": now})
            return True

        return bool(reserve(firestore_client.transaction()))

    def search_usage(self, now: datetime) -> int:
        snapshot = firestore_client.collection("artist_watch_usage").document(now.strftime("%Y-%m")).get()
        return (snapshot.to_dict() or {}).get("requests", 0)

    def queue_event(self, watch: ArtistWatch, event: ConcertEvent, token: str) -> None:
        parent = self._collection().document(watch._id)
        ref = parent.collection("events").document(event.key(watch.artist_name))

        @firestore.transactional
        def queue(tx):
            parent_snapshot = parent.get(transaction=tx)
            parent_data = parent_snapshot.to_dict() or {}
            if not parent_snapshot.exists or not parent_data.get("enabled") or parent_data.get("lease_token") != token:
                return
            snapshot = ref.get(transaction=tx)
            data = snapshot.to_dict() or {}
            current_event = event
            if snapshot.exists and not event.ticket_info and data.get("event", {}).get("ticket_info"):
                current_event = ConcertEvent(**{**event.__dict__, "ticket_info": data["event"]["ticket_info"]})
            if data.get("sent_fingerprint") == current_event.fingerprint:
                if data.get("pending"):
                    tx.update(ref, {"pending": False})
                return
            if data.get("pending") and data.get("fingerprint") == current_event.fingerprint:
                return
            # Each new change gets a persisted key; retries reuse it, status cycles do not.
            tx.set(ref, {"event": current_event.to_dict(), "artist_name": watch.artist_name,
                         "fingerprint": current_event.fingerprint, "retry_key": str(uuid4()), "pending": True,
                         "is_update": bool(data.get("sent_fingerprint")),
                         "updated_at": datetime.now(UTC)}, merge=True)

        queue(firestore_client.transaction())

    def pending_events(self, watch_id: str, artist_name: str) -> list[dict]:
        documents = self._collection().document(watch_id).collection("events").where("pending", "==", True).stream()
        return [{**doc.to_dict(), "_id": doc.id} for doc in documents if doc.to_dict().get("artist_name") == artist_name]

    def mark_sent(self, watch_id: str, event_id: str, fingerprint: str) -> None:
        ref = self._collection().document(watch_id).collection("events").document(event_id)

        @firestore.transactional
        def acknowledge(tx):
            snapshot = ref.get(transaction=tx)
            if snapshot.exists and snapshot.to_dict().get("fingerprint") == fingerprint:
                tx.update(ref, {"sent_fingerprint": fingerprint, "pending": False, "sent_at": datetime.now(UTC)})

        acknowledge(firestore_client.transaction())

    def discard_expired(self, watch_id: str, event_id: str) -> None:
        self._collection().document(watch_id).collection("events").document(event_id).update(
            {"pending": False, "discard_reason": "event_expired", "discarded_at": datetime.now(UTC)}
        )

    def delete_for_owner(self, owner_id: str) -> int:
        documents = self._collection().where("owner_id", "==", owner_id).stream()
        count = 0
        for document in documents:
            # Firestore does not cascade deletion into subcollections.
            # Remove the parent first, so in-progress scans cannot recreate history.
            document.reference.delete()
            for event in document.reference.collection("events").stream():
                event.reference.delete()
            count += 1
        return count
