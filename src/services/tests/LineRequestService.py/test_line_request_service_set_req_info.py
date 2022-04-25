import pytest
from services.LineRequestService import LineRequestService
from src.tests.dummies import (
    generate_dummy_follow_event,
    generate_dummy_text_message_event_from_user,
    generate_dummy_text_message_event_from_group,
)
from src.line_bot_api import line_bot_api
from src.tests.dummies import Profile


def test_follow_event(mocker):
    # Arrange
    line_request_service = LineRequestService()
    follow_event = generate_dummy_follow_event()
    mocker.patch.object(
        line_bot_api,
        'get_profile',
        return_value=Profile(
            display_name='dummy_display_name',
            user_id='dummy_user_id',
        ),
    )
    # Act
    line_request_service.set_req_info(follow_event)

    # Assert
    assert line_request_service.req_line_user_id == follow_event.source.user_id
    assert line_request_service.event_type == follow_event.type
    assert line_request_service.message_type is None
    assert line_request_service.message is None
    assert line_request_service.req_line_user_name == "dummy_display_name"


def test_follow_event_NG_cannot_get_user_profile():
    with pytest.raises(ValueError):
        # Arrange
        line_request_service = LineRequestService()
        follow_event = generate_dummy_follow_event()

        # Act
        line_request_service.set_req_info(follow_event)

        # Assert


def test_message_event_from_user(mocker):
    # Arrange
    line_request_service = LineRequestService()
    message_event = generate_dummy_text_message_event_from_user()
    mocker.patch.object(
        line_bot_api,
        'get_profile',
        return_value=Profile(
            display_name='dummy_display_name',
            user_id='dummy_user_id',
        ),
    )

    # Act
    line_request_service.set_req_info(message_event)

    # Assert
    assert line_request_service.req_line_user_id == message_event.source.user_id
    assert line_request_service.event_type == message_event.type
    assert line_request_service.message_type == message_event.message.type
    assert line_request_service.message == message_event.message.text


def test_message_event_from_group(mocker):
    # Arrange
    line_request_service = LineRequestService()
    message_event = generate_dummy_text_message_event_from_group()
    line_request_service = LineRequestService()
    mocker.patch.object(
        line_bot_api,
        'get_profile',
        return_value=Profile(
            display_name='dummy_display_name',
            user_id='dummy_user_id',
        ),
    )

    # Act
    line_request_service.set_req_info(message_event)

    # Assert
    assert line_request_service.req_line_user_id == message_event.source.user_id
    assert line_request_service.event_type == message_event.type
    assert line_request_service.message_type == message_event.message.type
    assert line_request_service.message == message_event.message.text
