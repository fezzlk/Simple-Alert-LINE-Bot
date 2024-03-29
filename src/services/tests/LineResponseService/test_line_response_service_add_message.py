from src.services.LineResponseService import LineResponseService


def test_success():
    # Arrange
    line_response_service = LineResponseService()

    # Act
    line_response_service.add_message('test')

    # Assert
    assert len(line_response_service.texts) == 1
    assert line_response_service.texts[0].text == 'test'


def test_success_multi_call():
    # Arrange
    line_response_service = LineResponseService()

    # Act
    line_response_service.add_message('test1')
    line_response_service.add_message('test2')
    line_response_service.add_message('test3')

    # Assert
    assert len(line_response_service.texts) == 3
    assert line_response_service.texts[0].text == 'test1'
    assert line_response_service.texts[1].text == 'test2'
    assert line_response_service.texts[2].text == 'test3'
