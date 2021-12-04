from src.Domains.Entities.LineUser import LineUser
from src.services import LineUserService
from src.tests.dummies import generate_dummy_line_user_list
from src.Infrastructure.Repositories import LineUserRepository


def test_success_not_exist():
    # Arrange
    line_user_service = LineUserService()
    line_user_repository = LineUserRepository()
    dummy_line_users = generate_dummy_line_user_list()[:3]
    target_line_user = dummy_line_users[0]
    other_line_users = dummy_line_users[1:]
    for other_user in other_line_users:
        line_user_repository.create(other_user)

    # Act
    result = line_user_service.find_or_create(
        new_line_user=target_line_user
    )

    # Assert
    assert isinstance(result, LineUser)
    assert result.line_user_name == target_line_user.line_user_name
    assert result.line_user_id == target_line_user.line_user_id

    records_in_db = line_user_repository.find()
    assert len(records_in_db) == len(dummy_line_users)


def test_success_exist():
    # Arrange
    line_user_service = LineUserService()
    line_user_repository = LineUserRepository()
    dummy_line_users = generate_dummy_line_user_list()[:3]
    for dummy_line_user in dummy_line_users:
        line_user_repository.create(dummy_line_user)
    target_line_user = dummy_line_users[0]

    # Act
    result = line_user_service.find_or_create(
        new_line_user=target_line_user
    )

    # Assert
    assert isinstance(result, LineUser)
    assert result.line_user_name == target_line_user.line_user_name
    assert result.line_user_id == target_line_user.line_user_id

    records_in_db = line_user_repository.find()
    assert len(records_in_db) == len(dummy_line_users)
