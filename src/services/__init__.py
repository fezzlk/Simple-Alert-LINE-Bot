from .LineRequestService import LineRequestService
from .LineResponseService import LineResponseService
from .TrainService import TrainService
from .WeatherService import WeatherService

line_response_service = LineResponseService()
line_request_service = LineRequestService()
train_service = TrainService()
weather_service = WeatherService()
