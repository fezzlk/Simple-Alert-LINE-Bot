from src.Domains.Entities.User import User
from src.Infrastructure.Repositories.UserRepository import UserRepository
from src.tests.dummies import generate_dummy_user_list


def test_success():
    # Arrange
    user_repository = UserRepository()
    dummy_users = generate_dummy_user_list()[:3]
    for dummy_user in dummy_users:
        user_repository.create(
            new_user=dummy_user,
        )
    target_users = dummy_users[:1]
    other_users = dummy_users[1:]
    query = {
        'user_name': target_users[0].user_name,
    }

    # Act
    result = user_repository.delete(query=query)

    # Assert
    assert result == len(target_users)
    records_in_db = user_repository.find()
    assert len(records_in_db) == len(other_users)
    for i in range(len(records_in_db)):
        assert records_in_db[i].user_name == other_users[i].user_name
        assert records_in_db[i].line_user_id == other_users[i].line_user_id
        assert records_in_db[i].line_user_name == other_users[i].line_user_name


def test_success_hit_all_records():
    # Arrange
    user_repository = UserRepository()
    dummy_users = generate_dummy_user_list()[:3]
    for dummy_user in dummy_users:
        user_repository.create(
            new_user=dummy_user,
        )

    # Act
    result = user_repository.delete()

    # Assert
    assert result == len(dummy_users)
    records_in_db = user_repository.find()
    assert len(records_in_db) == 0
