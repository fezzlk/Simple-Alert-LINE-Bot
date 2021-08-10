from linebot.models import TextSendMessage


def create_train_delay_message():
    return '電車遅延情報を取得'

def create_weather_message():
    return '天気情報を取得'

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
