from .LineRequestService import LineRequestService
from .LineResponseService import LineResponseService
from .TrainService import TrainService
from .WeatherService import WeatherService
from .LineUserService import LineUserService
from .WebUserService import WebUserService

line_response_service = LineResponseService()
line_request_service = LineRequestService()
train_service = TrainService()
weather_service = WeatherService()
line_user_service = LineUserService()
web_user_service = WebUserService()
