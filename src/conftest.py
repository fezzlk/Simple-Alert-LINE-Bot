# flake8: noqa
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv
from src.firestore_client import firestore_client
from src import app
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / '.env')


@pytest.fixture()
def dummy_app():
    return app


@pytest.fixture(scope='function', autouse=True)
def reset_db():
    if not os.getenv('FIRESTORE_EMULATOR_HOST'):
        return
    for collection_name in ['web_users', 'line_users', 'stocks']:
        for doc in firestore_client.collection(collection_name).stream():
            doc.reference.delete()
