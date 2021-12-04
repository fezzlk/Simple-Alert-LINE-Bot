from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    weather_service,
)


class ViewWeatherUseCase(IUseCase):
    def execute(self) -> str:
        return weather_service.get_weather()
