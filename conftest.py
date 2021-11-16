# flake8: noqa
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

load_dotenv()


# @pytest.fixture(scope='function', autouse=True)
# def reset_db():
#     db.collection.delete_many( { } );
