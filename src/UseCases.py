from typing import Dict, Callable
from .services import (
    weather_service,
    train_service,
    line_request_service,
    line_response_service,
)


def reply_train_delay() -> None:
    print('get train info')
    data = train_service.get_trains_delay_info()
    res = '運行情報\n'
    for name, info in data.items():
        res += '\n' + name + ':\n' + info + '\n'
    line_response_service.add_message(res)


def reply_weather() -> None:
    data = weather_service.get_weather()
    res = data['city'] + 'の天気\n'
    for date, info_of_the_day in data['data'].items():
        res += '\n' + date
        for time, info in info_of_the_day.items():
            res += '\n' ' '.join([time, str(info['temp']), info['weather']])
        res += '\n'
    line_response_service.add_message(res)


def register_stock() -> None:
    keyword, name, period = line_request_service.message.split('')
    line_response_service.add_message('在庫登録完了')


def reply_stock_list() -> None:
    line_response_service.add_message('在庫一覧を表示')


def text_message_use_case() -> None:
    '''
    受信メッセージから返信メッセージを生成
    '''
    print('receive text message')
    train_keywords: Dict[str, Callable] = {
        '遅延': reply_train_delay,
    }
    weather_keywords: Dict[str, Callable] = {
        '天気': reply_weather,
    }
    stock_keywords: Dict[str, Callable] = {
        '在庫登録': register_stock,
        '在庫一覧': reply_stock_list,
    }

    keyword = line_request_service.message.split()[0]
    # 電車情報
    if keyword in train_keywords:
        train_keywords[keyword]()
    # 天気情報
    elif keyword in weather_keywords:
        weather_keywords[keyword]()
    # 食材在庫情報
    elif keyword in stock_keywords:
        stock_keywords[keyword]()
    else:
        line_response_service.add_message(f'"{keyword}"というワードは登録されていません。')


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
