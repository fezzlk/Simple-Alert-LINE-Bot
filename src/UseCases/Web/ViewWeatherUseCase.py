from typing import Dict
from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    weather_service,
)


class ViewWeatherUseCase(IUseCase):
    def execute(self, page_contents: dict) -> Dict:
        page_contents['title'] = '天気情報'
        page_contents['data'] = weather_service.get_weather()
        return page_contents
