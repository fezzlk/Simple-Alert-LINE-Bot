from src.Domains.Entities.WebUser import WebUser
from src.Infrastructure.Repositories.WebUserRepository import WebUserRepository
from src.tests.dummies import generate_dummy_web_user_list


def test_success():
    # Arrange
    web_user_repository = WebUserRepository()
    dummy_web_users = generate_dummy_web_user_list()[:3]
    for dummy_web_user in dummy_web_users:
        web_user_repository.create(
            new_web_user=dummy_web_user,
        )
    target_web_users = dummy_web_users[:1]
    query = {
        'web_user_name': target_web_users[0].web_user_name,
    }

    # Act
    result = web_user_repository.find(query=query)

    # Assert
    assert len(result) == len(target_web_users)
    for i in range(len(result)):
        assert isinstance(result[i], WebUser)
        assert result[i].web_user_name == target_web_users[i].web_user_name
        assert result[i].web_user_email == target_web_users[i].web_user_email


def test_success_hit_all_records():
    # Arrange
    web_user_repository = WebUserRepository()
    dummy_web_users = generate_dummy_web_user_list()[:3]
    for dummy_web_user in dummy_web_users:
        web_user_repository.create(
            new_web_user=dummy_web_user,
        )

    # Act
    result = web_user_repository.find()

    # Assert
    assert len(result) == len(dummy_web_users)
    for i in range(len(result)):
        assert isinstance(result[i], WebUser)
        assert result[i].web_user_name == dummy_web_users[i].web_user_name
        assert result[i].web_user_email == dummy_web_users[i].web_user_email
