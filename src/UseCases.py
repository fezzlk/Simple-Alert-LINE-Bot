from typing import Dict, Callable
from .services import (
    weather_service,
    train_service,
    line_request_service,
    line_response_service,
)


def reply_train_delay() -> str:
    data = train_service.get_trains_delay_info()
    res = '運行情報\n'
    for name, info in data.items():
        res += '\n' + name + ':\n' + info + '\n'
    return res


def reply_weather() -> str:
    data = weather_service.get_weather()
    res = data['city'] + 'の天気\n'
    for date, info_of_the_day in data['data'].items():
        res += '\n' + date
        for time, info in info_of_the_day.items():
            res += '\n' ' '.join([time, str(info['temp']), info['weather']])
        res += '\n'
    return res


def register_stock() -> str:
    keyword, name, period = line_request_service.message.split('')
    return '在庫登録完了'


def text_message_use_case() -> None:
    message_type = line_request_service.message_type

    if message_type == 'text':
        '''
        受信メッセージから返信メッセージを生成
        '''
        train_keywords: Dict[str, Callable] = {
            '遅延': reply_train_delay
        }
        weather_keywords: Dict[str, Callable] = {
            '天気': reply_weather
        }
        stock_keywords: Dict[str, Callable] = {
            '在庫登録': register_stock
        }

        keyword = line_request_service.message.split('')[0]
        # 電車情報
        if keyword in train_keywords:
            line_response_service.add_message(train_keywords[keyword]())
        # 天気情報
        elif keyword in weather_keywords:
            line_response_service.add_message(weather_keywords[keyword]())
        # 食材在庫情報
        elif keyword in stock_keywords:
            line_response_service.add_message(stock_keywords[keyword]())
        else:
            line_response_service.add_message(f'"{keyword}"というワードは登録されていません。')
    else:
        line_response_service.add_message('現在はテキストメッセージのみ対応しています。')


def follow_use_case() -> None:
    line_response_service.add_message('現在はテキストメッセージのみ対応しています。')


def unfollow_use_case() -> None:
    line_response_service.add_message('現在はテキストメッセージのみ対応しています。')


def postback_use_case() -> None:
    line_response_service.add_message('現在はテキストメッセージのみ対応しています。')


def join_use_case() -> None:
    line_response_service.add_message('現在はテキストメッセージのみ対応しています。')


def image_message_use_case() -> None:
    line_response_service.add_message('現在はテキストメッセージのみ対応しています。')
