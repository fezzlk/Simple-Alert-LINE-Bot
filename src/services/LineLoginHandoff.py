"""One-use, browser-bound LINE login transfer. Never stores LINE tokens."""
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from src.firestore_client import firestore_client

LIFETIME = timedelta(minutes=5)
MAX_ATTEMPTS = 5
STATE_PATTERN = re.compile(r"h1\.[A-Za-z0-9_-]{43}\Z")


def now_utc():
    return datetime.now(timezone.utc)


def digest(state, purpose, value):
    key = current_app.secret_key
    if isinstance(key, str):
        key = key.encode()
    return hmac.new(key, f"{state}:{purpose}:{value}".encode(), hashlib.sha256).hexdigest()


class LineLoginHandoff:
    def _collection(self):
        return firestore_client.collection("line_login_handoffs")

    def _ref(self, state):
        if not isinstance(state, str) or not STATE_PATTERN.fullmatch(state):
            return None
        # Do not put OAuth state in document paths or database error messages.
        return self._collection().document(hashlib.sha256(state.encode()).hexdigest())

    def create(self, redirect_uri):
        state = "h1." + secrets.token_urlsafe(32)
        secret = secrets.token_urlsafe(32)
        verifier = secrets.token_urlsafe(48)
        now = now_utc()
        self._ref(state).create({
            "status": "pending", "expires_at": now + LIFETIME,
            "claim_hash": digest(state, "claim", secret),
            "verifier": verifier, "redirect_uri": redirect_uri,
        }, retry=None, timeout=5)
        return state, secret, verifier

    def cleanup(self):
        # Bounded, opportunistic cleanup; no paid TTL feature or new scheduler.
        expired = self._collection().where(filter=FieldFilter("expires_at", "<=", now_utc()))
        snapshots = list(expired.limit(20).select([]).stream(retry=None, timeout=5))
        if snapshots:
            batch = firestore_client.batch()
            for snapshot in snapshots:
                batch.delete(snapshot.reference)
            # A single bounded RPC, rather than up to 20 serial delete RPCs.
            batch.commit(retry=None, timeout=5)

    def for_owner(self, state, secret):
        ref = self._ref(state)
        if ref is None:
            return None
        data = ref.get(retry=None, timeout=5).to_dict() or {}
        if (data.get("expires_at", now_utc()) <= now_utc()
                or not hmac.compare_digest(data.get("claim_hash", ""), digest(state, "claim", secret))):
            return None
        return data

    def begin_callback(self, state):
        ref = self._ref(state)
        if ref is None:
            return None

        @firestore.transactional
        def begin(tx):
            data = ref.get(transaction=tx).to_dict() or {}
            if data.get("status") != "pending" or data.get("expires_at", now_utc()) <= now_utc():
                return None
            # Only one worker can exchange this authorization code.
            tx.update(ref, {"status": "exchanging"})
            return {"verifier": data["verifier"], "redirect_uri": data["redirect_uri"]}

        return begin(firestore_client.transaction())

    def complete_callback(self, state, profile, code):
        ref = self._ref(state)

        @firestore.transactional
        def complete(tx):
            data = ref.get(transaction=tx).to_dict() or {}
            if data.get("status") != "exchanging" or data.get("expires_at", now_utc()) <= now_utc():
                return False
            # Replace the document to discard the PKCE verifier immediately.
            tx.set(ref, {"status": "ready", "expires_at": data["expires_at"],
                         "claim_hash": data["claim_hash"], "attempts": 0,
                         "code_hash": digest(state, "code", code), "profile": profile})
            return True

        return complete(firestore_client.transaction())

    def consume(self, state, secret, code):
        ref = self._ref(state)
        if ref is None or not isinstance(secret, str) or not secret:
            return "invalid", None

        @firestore.transactional
        def consume_once(tx):
            data = ref.get(transaction=tx).to_dict() or {}
            if not hmac.compare_digest(data.get("claim_hash", ""), digest(state, "claim", secret)):
                return "invalid", None
            if data.get("expires_at", now_utc()) <= now_utc():
                tx.delete(ref)
                return "expired", None
            if data.get("status") in ("pending", "exchanging"):
                return "pending", None
            if data.get("status") != "ready":
                return "invalid", None
            if not hmac.compare_digest(data["code_hash"], digest(state, "code", code)):
                attempts = data["attempts"] + 1
                if attempts >= MAX_ATTEMPTS:
                    tx.delete(ref)
                    return "locked", None
                tx.update(ref, {"attempts": attempts})
                return "wrong_code", None
            tx.delete(ref)
            return "ok", data["profile"]

        return consume_once(firestore_client.transaction())

    def revoke(self, state, secret):
        ref = self._ref(state)
        if ref is None:
            return

        @firestore.transactional
        def revoke_owned(tx):
            data = ref.get(transaction=tx).to_dict() or {}
            if hmac.compare_digest(data.get("claim_hash", ""), digest(state, "claim", secret)):
                tx.delete(ref)

        revoke_owned(firestore_client.transaction())

    def fail_callback(self, state):
        # Called only after begin_callback successfully consumed the state.
        self._ref(state).delete(retry=None, timeout=5)
