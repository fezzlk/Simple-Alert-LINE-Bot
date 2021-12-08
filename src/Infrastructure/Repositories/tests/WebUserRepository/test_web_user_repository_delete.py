from src.Infrastructure.Repositories.WebUserRepository import WebUserRepository
from src.tests.dummies import generate_dummy_web_user_list


def test_success():
    # Arrange
    web_user_repository = WebUserRepository()
    dummy_web_users = generate_dummy_web_user_list()[:3]
    for dummy_user in dummy_web_users:
        web_user_repository.create(
            new_web_user=dummy_user,
        )
    target_web_users = dummy_web_users[:1]
    other_web_users = dummy_web_users[1:]
    query = {
        'web_user_name': target_web_users[0].web_user_name,
    }

    # Act
    result = web_user_repository.delete(query=query)

    # Assert
    assert result == len(target_web_users)
    records_in_db = web_user_repository.find()
    assert len(records_in_db) == len(other_web_users)
    for i in range(len(records_in_db)):
        assert records_in_db[i].web_user_name == other_web_users[i].web_user_name
        assert records_in_db[i].web_user_email == other_web_users[i].web_user_email


def test_success_hit_all_records():
    # Arrange
    web_user_repository = WebUserRepository()
    dummy_web_users = generate_dummy_web_user_list()[:3]
    for dummy_user in dummy_web_users:
        web_user_repository.create(
            new_web_user=dummy_user,
        )

    # Act
    result = web_user_repository.delete()

    # Assert
    assert result == len(dummy_web_users)
    records_in_db = web_user_repository.find()
    assert len(records_in_db) == 0
