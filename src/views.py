from flask import request, abort
from linebot.exceptions import InvalidSignatureError
from src import app, line, handler
from src.message import create_message

from linebot.models import (
    MessageEvent, TextMessage,
)

'''
Endpoints for Web
'''


@app.route('/', methods=['GET'])
def route():
    return 'Hello, world!'


'''
Endpoints for LINE Bot
'''


@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info('Request body: ' + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


'''
handle event
'''


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    user_id = event.source.user_id
    user_name = line.get_profile(user_id).display_name
    print(f"Received message: \"{message}\" from {user_name}")
    reply_content = create_message(user_id, message)
    line.reply_message(event.reply_token, reply_content)
