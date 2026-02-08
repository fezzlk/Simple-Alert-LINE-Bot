from src import config
from google.cloud import firestore


def get_firestore_client() -> firestore.Client:
    if config.FIRESTORE_PROJECT_ID:
        return firestore.Client(project=config.FIRESTORE_PROJECT_ID)
    return firestore.Client()


firestore_client = get_firestore_client()
