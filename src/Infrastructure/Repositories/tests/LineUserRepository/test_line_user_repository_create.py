from src.Domains.Entities.LineUser import LineUser
from src.Infrastructure.Repositories.LineUserRepository import LineUserRepository
from src.tests.dummies import generate_dummy_line_user_list


def test_success():
    # Arrange
    line_user_repository = LineUserRepository()
    dummy_line_user = generate_dummy_line_user_list()[0]

    # Act
    result = line_user_repository.create(
        new_line_user=dummy_line_user
    )

    # Assert
    assert isinstance(result, LineUser)
    assert result.line_user_name == dummy_line_user.line_user_name
    assert result.line_user_id == dummy_line_user.line_user_id
