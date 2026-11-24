from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import date, datetime, timezone
from threading import RLock
from uuid import uuid4

import pytest

from src.Domains.Entities.ArtistWatch import ConcertEvent
from src.Infrastructure.Repositories import ArtistWatchRepository as repository_class
from src.Infrastructure.Repositories.ArtistWatchRepository import MONTHLY_SEARCH_LIMIT

NOW = datetime(2026, 11, 22, tzinfo=timezone.utc)


class Snapshot:
    def __init__(self, ref):
        self.reference = ref
        self.id = ref.id
        self.exists = ref.path in ref.db.data
        self.data = deepcopy(ref.db.data.get(ref.path, {}))

    def to_dict(self):
        return self.data


class Reference:
    def __init__(self, db, path):
        self.db = db
        self.path = path
        self.id = path[-1]

    def get(self, transaction=None):
        return Snapshot(self)

    def set(self, data, merge=False):
        previous = self.db.data.get(self.path, {}) if merge else {}
        self.db.data[self.path] = {**previous, **deepcopy(data)}

    def update(self, data):
        if self.path not in self.db.data:
            raise LookupError
        self.set(data, merge=True)

    def collection(self, name):
        return Collection(self.db, (*self.path, name))

    def delete(self):
        self.db.data.pop(self.path, None)


class Collection:
    def __init__(self, db, path, filters=(), projection=None):
        self.db = db
        self.path = path
        self.filters = filters
        self.projection = projection

    def document(self, doc_id=None):
        return Reference(self.db, (*self.path, doc_id or str(uuid4())))

    def where(self, field, op, value):
        assert op == "=="
        return Collection(self.db, self.path, (*self.filters, (field, value)), self.projection)

    def select(self, fields):
        return Collection(self.db, self.path, self.filters, tuple(fields))

    def stream(self):
        snapshots = []
        for path, data in list(self.db.data.items()):
            if path[:-1] == self.path and all(data.get(field) == value for field, value in self.filters):
                snapshot = Snapshot(Reference(self.db, path))
                if self.projection is not None:
                    snapshot.data = {key: value for key, value in snapshot.data.items() if key in self.projection}
                snapshots.append(snapshot)
        return iter(snapshots)


class Database:
    def __init__(self):
        self.data = {}
        self.lock = RLock()

    def collection(self, name):
        return Collection(self, (name,))

    def transaction(self):
        return self

    def set(self, ref, data, merge=False):
        ref.set(data, merge)

    def update(self, ref, data):
        ref.update(data)


@pytest.fixture
def database(monkeypatch):
    import importlib
    module = importlib.import_module("src.Infrastructure.Repositories.ArtistWatchRepository")
    db = Database()

    def transactional(function):
        def run(tx):
            with tx.lock:
                return function(tx)
        return run

    monkeypatch.setattr(module, "firestore_client", db)
    monkeypatch.setattr(module.firestore, "transactional", transactional)
    return db


def test_global_budget_survives_instances_and_concurrent_reservations(database):
    database.collection("artist_watch_usage").document("2026-11").set({"requests": MONTHLY_SEARCH_LIMIT - 1})
    with ThreadPoolExecutor(max_workers=8) as pool:
        reservations = list(pool.map(lambda _: repository_class().reserve_search(NOW), range(20)))
    assert sum(reservations) == 1
    assert repository_class().search_usage(NOW) == MONTHLY_SEARCH_LIMIT
    assert repository_class().reserve_search(datetime(2026, 12, 1, tzinfo=timezone.utc))


def test_claim_excludes_overlapping_worker_and_finish_requires_token(database):
    ref = database.collection("artist_watches").document("A1")
    ref.set({"owner_id": "W1", "artist_name": "Chris Dave", "enabled": True})
    repo = repository_class()
    _, token = repo.claim("A1", NOW)
    assert token
    assert repo.claim("A1", NOW) is None
    repo.finish("A1", "wrong-token", status="incorrect")
    assert ref.get().to_dict().get("status") is None
    repo.finish("A1", token, status="ok")
    assert ref.get().to_dict()["status"] == "ok"


def test_other_owner_cannot_edit_or_stop_watch(database):
    repo = repository_class()
    watch_id = repo.save("W1", "Chris Dave", [], [])
    with pytest.raises(LookupError):
        repo.save("W2", "Other artist", [], [], watch_id)
    with pytest.raises(LookupError):
        repo.set_enabled("W2", watch_id, False)
    assert repo.list_for_owner("W1")[0].artist_name == "Chris Dave"
    assert repo.list_for_owner("W2") == []


def test_notification_dedup_and_material_update_preserve_retry_key(database):
    repo = repository_class()
    watch_id = repo.save("W1", "Chris Dave", [], [])
    watch = repo.list_for_owner("W1")[0]
    _, token = repo.claim(watch_id, NOW.replace(year=2030))
    event = ConcertEvent("Chris Dave", date(2027, 1, 8), "Billboard Live Tokyo", "https://example.com/show")
    repo.queue_event(watch, event, token)
    original = repo.pending_events(watch_id, watch.artist_name)[0]
    repo.queue_event(watch, event, token)
    assert repo.pending_events(watch_id, watch.artist_name)[0]["retry_key"] == original["retry_key"]
    repo.mark_sent(watch_id, original["_id"], original["fingerprint"])
    repo.queue_event(watch, event, token)
    assert repo.pending_events(watch_id, watch.artist_name) == []
    cancelled = ConcertEvent(**{**event.__dict__, "status": "cancelled"})
    repo.queue_event(watch, cancelled, token)
    updated = repo.pending_events(watch_id, watch.artist_name)[0]
    assert updated["is_update"]
    assert updated["retry_key"] != original["retry_key"]


def test_withdraw_deletes_nested_events_and_preserves_other_users(database):
    repo = repository_class()
    first = repo.save("W1", "Chris Dave", [], [])
    second = repo.save("W2", "Other artist", [], [])
    database.collection("artist_watches").document(first).collection("events").document("E1").set({"pending": True})
    assert repo.delete_for_owner("W1") == 1
    assert not any(first in path for path in database.data)
    assert database.collection("artist_watches").document(second).get().exists


def test_edit_invalidates_old_scan_and_claim_reads_latest_artist(database):
    repo = repository_class()
    watch_id = repo.save("W1", "Chris Dave", [], [])
    watch, old_token = repo.claim(watch_id, NOW.replace(year=2030))
    repo.save("W1", "Ben Wendel", [], [], watch_id)
    assert not repo.current(watch_id, old_token)
    latest, _ = repo.claim(watch_id, NOW.replace(year=2030))
    assert latest.artist_name == "Ben Wendel"
    event = ConcertEvent("Chris Dave", date(2027, 1, 8), "Billboard Live Tokyo", "https://example.com/show")
    repo.queue_event(watch, event, old_token)
    assert repo.pending_events(watch_id, "Chris Dave") == []


def test_withdraw_during_scan_cannot_recreate_orphan_history(database):
    repo = repository_class()
    watch_id = repo.save("W1", "Chris Dave", [], [])
    watch, token = repo.claim(watch_id, NOW.replace(year=2030))
    repo.delete_for_owner("W1")
    event = ConcertEvent("Chris Dave", date(2027, 1, 8), "Billboard Live Tokyo", "https://example.com/show")
    repo.queue_event(watch, event, token)
    assert not any(watch_id in path for path in database.data)


def test_reinstated_show_gets_new_retry_key_after_cancelled_notification(database):
    repo = repository_class()
    watch_id = repo.save("W1", "Chris Dave", [], [])
    watch, token = repo.claim(watch_id, NOW.replace(year=2030))
    event = ConcertEvent("Chris Dave", date(2027, 1, 8), "Billboard Live Tokyo", "https://example.com/show")
    keys = []
    for state in ("scheduled", "cancelled", "scheduled"):
        repo.queue_event(watch, ConcertEvent(**{**event.__dict__, "status": state}), token)
        item = repo.pending_events(watch_id, watch.artist_name)[0]
        keys.append(item["retry_key"])
        repo.mark_sent(watch_id, item["_id"], item["fingerprint"])
    assert len(set(keys)) == 3


def test_minute_poll_omits_history_but_claim_preserves_the_full_previous_record(database):
    ref = database.collection("artist_watches").document("A1")
    history = [{"url": "https://example.com/show", "title": "Chris Dave concert", "status": "ok"}]
    ref.set({"owner_id": "W1", "artist_name": "Chris Dave", "enabled": True, "last_page_checks": history})
    repo = repository_class()
    due = repo.due_watches(NOW)
    assert len(due) == 1
    assert due[0].last_page_checks == []
    claimed, _ = repo.claim("A1", NOW)
    assert claimed.last_page_checks == history
