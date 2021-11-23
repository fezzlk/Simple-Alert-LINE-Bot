from src.Domains.Entities.User import User
from src.services import UserService
from src.tests.dummies import generate_dummy_user_list
from src.Infrastructure.Repositories import UserRepository


def test_success_not_exist():
    # Arrange
    user_service = UserService()
    user_repository = UserRepository()
    dummy_users = generate_dummy_user_list()[:3]
    target_user = dummy_users[0]
    other_users = dummy_users[1:]
    for other_user in other_users:
        user_repository.create(other_user)

    # Act
    result = user_service.find_or_create(
        new_user=target_user
    )

    # Assert
    assert isinstance(result, User)
    assert result.user_name == target_user.user_name
    assert result.line_user_name == target_user.line_user_name
    assert result.line_user_id == target_user.line_user_id

    records_in_db = user_repository.find()
    assert len(records_in_db) == len(dummy_users)


def test_success_exist():
    # Arrange
    user_service = UserService()
    user_repository = UserRepository()
    dummy_users = generate_dummy_user_list()[:3]
    for dummy_user in dummy_users:
        user_repository.create(dummy_user)
    target_user = dummy_users[0]

    # Act
    result = user_service.find_or_create(
        new_user=target_user
    )

    # Assert
    assert isinstance(result, User)
    assert result.user_name == target_user.user_name
    assert result.line_user_name == target_user.line_user_name
    assert result.line_user_id == target_user.line_user_id

    records_in_db = user_repository.find()
    assert len(records_in_db) == len(dummy_users)
