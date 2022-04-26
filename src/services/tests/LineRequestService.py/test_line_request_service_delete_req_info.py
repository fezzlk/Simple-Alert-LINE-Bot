from src.services.LineRequestService import LineRequestService
from src.tests.dummies import (
    generate_dummy_follow_event,
)
from src.line_bot_api import line_bot_api
from src.tests.dummies import Profile


def test_success(mocker):
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
    line_request_service.set_req_info(follow_event)

    # Act
    line_request_service.delete_req_info()

    # Assert
    assert line_request_service.req_line_user_id is None
    assert line_request_service.req_line_group_id is None
    assert line_request_service.event_type is None
    assert line_request_service.message is None
    assert line_request_service.req_line_user_name is None
