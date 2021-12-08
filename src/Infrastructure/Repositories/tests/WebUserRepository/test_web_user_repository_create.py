from src.Domains.Entities.WebUser import WebUser
from src.Infrastructure.Repositories.WebUserRepository import WebUserRepository
from src.tests.dummies import generate_dummy_web_user_list


def test_success():
    # Arrange
    web_user_repository = WebUserRepository()
    dummy_web_user = generate_dummy_web_user_list()[0]

    # Act
    result = web_user_repository.create(
        new_web_user=dummy_web_user
    )

    # Assert
    assert isinstance(result, WebUser)
    assert result.web_user_name == dummy_web_user.web_user_name
    assert result.web_user_email == dummy_web_user.web_user_email
