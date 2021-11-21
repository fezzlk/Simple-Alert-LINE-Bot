from src import config
from pymongo import MongoClient

mongo_client = MongoClient(config.MONGO_URI)