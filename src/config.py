import os
from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv('DEBUG')
LINEBOT_CHANNEL_SECRET = os.getenv('LINEBOT_CHANNEL_SECRET')
LINEBOT_CHANNEL_ACCESS_TOKEN = os.getenv('LINEBOT_CHANNEL_ACCESS_TOKEN')
OPEN_WEATHER_MAP_API_KEY = os.getenv('OPEN_WEATHER_MAP_API_KEY')
MONGO_URI = os.getenv('MONGO_URI')
