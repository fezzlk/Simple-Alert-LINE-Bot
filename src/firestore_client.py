from src import config
from google.cloud import firestore


def get_firestore_client() -> firestore.Client:
    if config.FIRESTORE_PROJECT_ID:
        return firestore.Client(project=config.FIRESTORE_PROJECT_ID)
    return firestore.Client()


class _LazyFirestoreClient:
    def __init__(self) -> None:
        self._client = None

    def _get(self) -> firestore.Client:
        if self._client is None:
            self._client = get_firestore_client()
        return self._client

    def __getattr__(self, name):
        return getattr(self._get(), name)


firestore_client = _LazyFirestoreClient()
