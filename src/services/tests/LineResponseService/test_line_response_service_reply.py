import pytest
from services.LineResponseService import LineResponseService
from src.tests.dummies import (
    generate_dummy_follow_event,
    generate_dummy_text_message_event_from_user,
    generate_dummy_text_message_event_from_group,
)
from src.line_bot_api import line_bot_api
from src.models.Line.Event import Event
from linebot.models import (
    TextSendMessage,
    ImageSendMessage,
    TemplateSendMessage,
    ButtonsTemplate,
    PostbackAction,
)


@pytest.fixture(params=[
    (
        [TextSendMessage(text='hoge')],
        1,
    ),
    (
        [
            TextSendMessage(text='hoge'),
            TextSendMessage(text='fuga'),
        ],
        2,
    ),
])
def text_case(request) -> int:
    return request.param


def test_reply_success_with_text(text_case, mocker):
    # Arrange
    line_response_service = LineResponseService()
    dummy_event = Event(
        event_type='message',
        source_type='user',
        user_id='U0123456789abcdefghijklmnopqrstu1',
        message_type='text',
        text='dummy_text',
    )
    mock = mocker.patch.object(
        line_bot_api,
        'reply_message',
        return_value=None,
    )
    line_response_service.texts = text_case[0]

    # Act
    line_response_service.reply(dummy_event)

    # Assert
    args = mock.call_args_list[0]
    assert len(args[0][1]) == text_case[1]
    assert len(line_response_service.texts) == 0
    assert len(line_response_service.images) == 0
    assert len(line_response_service.buttons) == 0


@pytest.fixture(params=[
    (
        [ImageSendMessage(
            original_content_url='dummy_image_url',
            preview_image_url='dummy_image_url',
        )],
        1,
    ),
    (
        [
            ImageSendMessage(
                original_content_url='dummy_image_url1',
                preview_image_url='dummy_image_url1',
            ),
            ImageSendMessage(
                original_content_url='dummy_image_url2',
                preview_image_url='dummy_image_url2',
            ),
        ],
        2,
    ),
])
def image_case(request) -> int:
    return request.param


def test_reply_success_with_image(image_case, mocker):
    # Arrange
    line_response_service = LineResponseService()
    dummy_event = Event(
        event_type='message',
        source_type='user',
        user_id='U0123456789abcdefghijklmnopqrstu1',
        message_type='text',
        text='dummy_text',
    )
    mock = mocker.patch.object(
        line_bot_api,
        'reply_message',
        return_value=None,
    )
    line_response_service.images = image_case[0]

    # Act
    line_response_service.reply(dummy_event)

    # Assert
    args = mock.call_args_list[0]
    assert len(args[0][1]) == image_case[1]
    assert len(line_response_service.texts) == 0
    assert len(line_response_service.images) == 0
    assert len(line_response_service.buttons) == 0


@pytest.fixture(params=[
    (
        [TemplateSendMessage(
            alt_text='hoge',
            template=ButtonsTemplate(
                title='hoge',
                text='hoge',
                actions=[
                    PostbackAction(
                        label='hoge',
                        display_text='hoge',
                        data='hoge'
                    ),
                ]
            )
        )],
        1,
    ),
    (
        [
            TemplateSendMessage(
                alt_text='hoge',
                template=ButtonsTemplate(
                    title='hoge',
                    text='hoge',
                    actions=[
                        PostbackAction(
                            label='hoge',
                            display_text='hoge',
                            data='hoge'
                        ),
                    ]
                )
            ),
            TemplateSendMessage(
                alt_text='fuga',
                template=ButtonsTemplate(
                    title='fuga',
                    text='fuga',
                    actions=[
                        PostbackAction(
                            label='fuga',
                            display_text='fuga',
                            data='fuga'
                        ),
                    ]
                )
            ),
        ],
        2,
    ),
])
def button_case(request) -> int:
    return request.param


def test_reply_success_with_text(button_case, mocker):
    # Arrange
    line_response_service = LineResponseService()
    dummy_event = Event(
        event_type='message',
        source_type='user',
        user_id='U0123456789abcdefghijklmnopqrstu1',
        message_type='text',
        text='dummy_text',
    )
    mock = mocker.patch.object(
        line_bot_api,
        'reply_message',
        return_value=None,
    )
    line_response_service.buttons = button_case[0]

    # Act
    line_response_service.reply(dummy_event)

    # Assert
    args = mock.call_args_list[0]
    assert len(args[0][1]) == button_case[1]
    assert len(line_response_service.texts) == 0
    assert len(line_response_service.images) == 0
    assert len(line_response_service.buttons) == 0


@pytest.fixture(params=[
    (
        [TextSendMessage(text='hoge')],
        1,
    ),
    (
        [
            TextSendMessage(text='hoge'),
            TextSendMessage(text='fuga'),
        ],
        2,
    ),
])
def text_case(request) -> int:
    return request.param


def test_reply_success_with_multi_contents(mocker):
    # Arrange
    line_response_service = LineResponseService()
    dummy_event = Event(
        event_type='message',
        source_type='user',
        user_id='U0123456789abcdefghijklmnopqrstu1',
        message_type='text',
        text='dummy_text',
    )
    mock = mocker.patch.object(
        line_bot_api,
        'reply_message',
        return_value=None,
    )
    line_response_service.texts = [TextSendMessage(text='hoge')]
    line_response_service.images = [ImageSendMessage(
        original_content_url='dummy_image_url',
        preview_image_url='dummy_image_url',
    )]
    line_response_service.buttons = [TemplateSendMessage(
        alt_text='fuga',
        template=ButtonsTemplate(
            title='fuga',
            text='fuga',
            actions=[
                PostbackAction(
                    label='fuga',
                    display_text='fuga',
                    data='fuga'
                ),
            ]
        )
    )]

    # Act
    line_response_service.reply(dummy_event)

    # Assert
    args = mock.call_args_list[0]
    assert len(args[0][1]) == 3
    assert len(line_response_service.texts) == 0
    assert len(line_response_service.images) == 0
    assert len(line_response_service.buttons) == 0


def test_reply_success_with_no_content(mocker):
    # Arrange
    line_response_service = LineResponseService()
    dummy_event = Event(
        event_type='message',
        source_type='user',
        user_id='U0123456789abcdefghijklmnopqrstu1',
        message_type='text',
        text='dummy_text',
    )
    mock = mocker.patch.object(
        line_bot_api,
        'reply_message',
        return_value=None,
    )

    # Act
    line_response_service.reply(dummy_event)

    # Assert
    mock.assert_not_called()
    assert len(line_response_service.texts) == 0
    assert len(line_response_service.images) == 0
    assert len(line_response_service.buttons) == 0


def test_reply_success_with_no_reply_token(mocker):
    # Arrange
    line_response_service = LineResponseService()
    dummy_event = Event(
        event_type='unfollow',
        source_type='user',
        user_id='U0123456789abcdefghijklmnopqrstu1',
        message_type='text',
        text='dummy_text',
    )
    mock = mocker.patch.object(
        line_bot_api,
        'reply_message',
        return_value=None,
    )
    line_response_service.texts = [TextSendMessage(text='hoge')]

    # Act
    line_response_service.reply(dummy_event)

    # Assert
    mock.assert_not_called()
    assert len(line_response_service.texts) == 0
    assert len(line_response_service.images) == 0
    assert len(line_response_service.buttons) == 0
