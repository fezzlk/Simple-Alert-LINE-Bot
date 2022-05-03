from src.services.LineResponseService import LineResponseService


def test_success():
    # Arrange
    line_response_service = LineResponseService()

    # Act
    line_response_service.add_image('test')

    # Assert
    assert len(line_response_service.images) == 1
    assert line_response_service.images[0].original_content_url == 'test'
    assert line_response_service.images[0].preview_image_url == 'test'


def test_success_multi_call():
    # Arrange
    line_response_service = LineResponseService()

    # Act
    line_response_service.add_image('test1')
    line_response_service.add_image('test2')
    line_response_service.add_image('test3')

    # Assert
    assert len(line_response_service.images) == 3
    assert line_response_service.images[0].original_content_url == 'test1'
    assert line_response_service.images[1].original_content_url == 'test2'
    assert line_response_service.images[2].original_content_url == 'test3'
    assert line_response_service.images[0].preview_image_url == 'test1'
    assert line_response_service.images[1].preview_image_url == 'test2'
    assert line_response_service.images[2].preview_image_url == 'test3'
