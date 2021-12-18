from src.Domains.Entities.WebUser import WebUser
from src.services import WebUserService
from src.tests.dummies import generate_dummy_web_user_list
from src.Infrastructure.Repositories import WebUserRepository


def test_success_not_exist():
    # Arrange
    web_user_service = WebUserService()
    web_user_repository = WebUserRepository()
    dummy_web_users = generate_dummy_web_user_list()[:3]
    target_web_user = dummy_web_users[0]
    other_web_users = dummy_web_users[1:]
    for other_user in other_web_users:
        web_user_repository.create(other_user)

    # Act
    result = web_user_service.find_or_create(
        new_web_user=target_web_user
    )

    # Assert
    assert isinstance(result, WebUser)
    assert result.web_user_name == target_web_user.web_user_name
    assert result.web_user_email == target_web_user.web_user_email

    records_in_db = web_user_repository.find()
    assert len(records_in_db) == len(dummy_web_users)


def test_success_exist():
    # Arrange
    web_user_service = WebUserService()
    web_user_repository = WebUserRepository()
    dummy_web_users = generate_dummy_web_user_list()[:3]
    for dummy_web_user in dummy_web_users:
        web_user_repository.create(dummy_web_user)
    target_web_user = dummy_web_users[0]

    # Act
    result = web_user_service.find_or_create(
        new_web_user=target_web_user
    )

    # Assert
    assert isinstance(result, WebUser)
    assert result.web_user_name == target_web_user.web_user_name
    assert result.web_user_email == target_web_user.web_user_email

    records_in_db = web_user_repository.find()
    assert len(records_in_db) == len(dummy_web_users)
