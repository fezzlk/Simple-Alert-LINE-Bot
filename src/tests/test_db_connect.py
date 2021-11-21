from typing import List
from src.mongo_client import mongo_client


def test_connect_mongo_with():
    assert isinstance(mongo_client.db.list_collection_names(), List)
