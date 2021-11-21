from src.Domains.Entities.User import User
from src.Infrastructure.Repositories.UserRepository import UserRepository
from src.tests.dummies import generate_dummy_user_list


def test_success():
    # Arrange
    user_repository = UserRepository()
    dummy_user = generate_dummy_user_list()[0]

    # Act
    result = user_repository.create(
        new_user=dummy_user
    )

    # Assert
    assert isinstance(result, User)
    assert result.user_name == dummy_user.user_name
    assert result.line_user_name == dummy_user.line_user_name
    assert result.line_user_id == dummy_user.line_user_id
