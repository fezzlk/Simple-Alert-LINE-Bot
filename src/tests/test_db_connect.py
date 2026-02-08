from google.cloud.firestore import Client
from src.firestore_client import firestore_client


def test_connect_firestore():
    assert isinstance(firestore_client, Client)
