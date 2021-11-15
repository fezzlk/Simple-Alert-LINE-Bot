from typing import Dict
from linebot.models import TextSendMessage
from .services import weather, train


def create_train_delay_message() -> str:
    data = train.get_trains_delay_info()
    res = '運行情報\n'
    for name, info in data.items():
        res += '\n' + name + ':\n' + info + '\n'
    return res


def create_weather_message() -> str:
    data = weather.get_weather()
    res = data['city'] + 'の天気\n'
    for date, info_of_the_day in data['data'].items():
        res += '\n' + date
        for time, info in info_of_the_day.items():
            res += '\n' ' '.join([time, str(info['temp']), info['weather']])
        res += '\n'
    return res


def create_register_stock_message(message: str) -> str:
    keyword, name, period = message.split('')
    return '在庫登録完了'


def create_message(user_id, message: str) -> TextSendMessage:
    '''
    受信メッセージから返信メッセージを生成
    '''
    train_keywords: Dict[str, function] = {
        '遅延': create_train_delay_message
    }
    weather_keywords: Dict[str, function] = {
        '天気': create_weather_message
    }
    stock_keywords: Dict[str, function] = {
        '在庫登録': create_register_stock_message
    }

    keyword = message.split('')[0]
    # 電車情報
    if keyword in train_keywords:
        return TextSendMessage(text=train_keywords[keyword]())
    # 天気情報
    elif keyword in weather_keywords:
        return TextSendMessage(text=weather_keywords[keyword]())
    # 食材在庫情報
    elif keyword in stock_keywords:
        return TextSendMessage(text=stock_keywords[keyword](message))
    else:
        return TextSendMessage(text=f'"{keyword}"というワードは登録されていません。')
