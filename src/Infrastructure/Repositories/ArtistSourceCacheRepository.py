from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

from google.cloud import firestore

from src.Domains.ArtistSourceCatalog import CATALOG_VERSION, source_id
from src.firestore_client import firestore_client

UTC = timezone.utc
INDEX_FIELDS = ("url", "title", "status", "reason", "checked_at", "text_z", "page_count", "failed_pages", "page_checks")


class ArtistSourceCacheRepository:
    """Public pages only: no user IDs, watch names or paid search responses."""
    def _collection(self):
        return firestore_client.collection("artist_source_cache")

    def claim_next(self, sources, now: datetime):
        ref = firestore_client.collection("artist_source_state").document("daily")
        day = now.astimezone(ZoneInfo("Asia/Tokyo")).date().isoformat()
        token = str(uuid4())

        @firestore.transactional
        def claim(tx):
            data = ref.get(transaction=tx).to_dict() or {}
            if data.get("lease_until") and data["lease_until"] > now:
                return None
            same_run = data.get("day") == day and data.get("catalog_version") == CATALOG_VERSION
            cursor = data.get("cursor", 0) if same_run else 0
            if cursor >= len(sources) or (same_run and data.get("next_at") and data["next_at"] > now):
                return None
            tx.set(ref, {"day": day, "catalog_version": CATALOG_VERSION, "cursor": cursor,
                         "lease_token": token, "lease_until": now + timedelta(seconds=55),
                         "next_at": (now + timedelta(minutes=1)).replace(second=0, microsecond=0)})
            return sources[cursor], token

        return claim(firestore_client.transaction())

    def finish(self, source, token: str, snapshot: dict, now: datetime):
        state_ref = firestore_client.collection("artist_source_state").document("daily")
        cache_ref = self._collection().document(source_id(source["url"]))

        @firestore.transactional
        def finish(tx):
            state = state_ref.get(transaction=tx).to_dict() or {}
            if state.get("lease_token") != token:
                return
            tx.set(cache_ref, {**snapshot, "url": source["url"], "checked_at": now})
            tx.update(state_ref, {"cursor": state["cursor"] + 1, "lease_token": "", "lease_until": None})

        finish(firestore_client.transaction())

    def index(self, include_text=True):
        fields = INDEX_FIELDS if include_text else tuple(field for field in INDEX_FIELDS if field != "text_z")
        return {data["url"]: data for doc in self._collection().select(fields).stream(retry=None, timeout=5)
                if (data := doc.to_dict()).get("url")}

    def pages(self, url, timeout=3):
        return (self._collection().document(source_id(url)).get(
            field_paths=["pages_z"], retry=None, timeout=timeout
        ).to_dict() or {}).get("pages_z")
