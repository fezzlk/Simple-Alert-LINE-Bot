from typing import Dict
from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    weather_service,
)
from src.models.PageContents import PageContents


class ViewWeatherUseCase(IUseCase):
    def execute(self, page_contents: PageContents) -> Dict:
        page_contents.page_title = '天気情報'
        page_contents.data = weather_service.get_weather()
        return page_contents
