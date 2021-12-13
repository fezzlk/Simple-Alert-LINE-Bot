from flask import session
from typing import Dict
from src.UseCases.Interface.IUseCase import IUseCase
from src.services import (
    weather_service,
)


class ViewWeatherUseCase(IUseCase):
    def execute(self) -> Dict:
        page_contents = {
            'title': 'weather',
            'login_email': dict(session).get('login_email', ''),
            'data': weather_service.get_weather(),
        }
        return page_contents
