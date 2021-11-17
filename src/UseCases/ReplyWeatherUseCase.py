from src.services import (
    weather_service,
    line_response_service,
)


class ReplyWeatherUseCase:
    def execute(self) -> None:
        data = weather_service.get_weather()
        res = data['city'] + 'の天気\n'
        for date, info_of_the_day in data['data'].items():
            res += '\n' + date
            for time, info in info_of_the_day.items():
                res += '\n' ' '.join([time, str(info['temp']),
                                     info['weather']])
            res += '\n'
        line_response_service.add_message(res)
