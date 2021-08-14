from linebot.models import TextSendMessage
from .functions import weather, train


def create_train_delay_message():
    data = train.get_trains_delay_info()
    res = '運行情報\n'
    for name, info in data.items():
        res += '\n' + name + ':\n' + info + '\n'
    return res


def create_weather_message():
    data = weather.get_weather()
    res = data['city'] + 'の天気\n'
    for date, info_of_the_day in data['data'].items():
        res += '\n' + date
        for time, info in info_of_the_day.items():
            res += '\n' ' '.join([time, str(info['temp']), info['weather']])
        res += '\n'
    return res


def create_message(user_id, message):
    '''
    受信メッセージから返信メッセージを生成
    '''
    train_keywords = {
        '遅延': create_train_delay_message()
    }
    weather_keywords = {
        '天気': create_weather_message()
    }

    # 電車情報
    if message in train_keywords:
        return TextSendMessage(text=train_keywords[message])
    # 天気情報
    elif message in weather_keywords:
        return TextSendMessage(text=weather_keywords[message])
    else:
        return TextSendMessage(text=f'"{message}"というワードは登録されていません。')
