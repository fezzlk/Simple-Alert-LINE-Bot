from src.firestore_client import firestore_client


def test_connect_firestore():
    # Accessing the method should initialize the underlying client (emulator or ADC).
    assert hasattr(firestore_client, "collection")
