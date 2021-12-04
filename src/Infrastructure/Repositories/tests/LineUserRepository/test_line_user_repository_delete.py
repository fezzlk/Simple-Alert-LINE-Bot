from src.Domains.Entities.LineUser import LineUser
from src.Infrastructure.Repositories.LineUserRepository import LineUserRepository
from src.tests.dummies import generate_dummy_line_user_list


def test_success():
    # Arrange
    line_user_repository = LineUserRepository()
    dummy_line_users = generate_dummy_line_user_list()[:3]
    for dummy_user in dummy_line_users:
        line_user_repository.create(
            new_line_user=dummy_user,
        )
    target_line_users = dummy_line_users[:1]
    other_line_users = dummy_line_users[1:]
    query = {
        'line_user_id': target_line_users[0].line_user_id,
    }

    # Act
    result = line_user_repository.delete(query=query)

    # Assert
    assert result == len(target_line_users)
    records_in_db = line_user_repository.find()
    assert len(records_in_db) == len(other_line_users)
    for i in range(len(records_in_db)):
        assert records_in_db[i].line_user_id == other_line_users[i].line_user_id
        assert records_in_db[i].line_user_name == other_line_users[i].line_user_name


def test_success_hit_all_records():
    # Arrange
    line_user_repository = LineUserRepository()
    dummy_line_users = generate_dummy_line_user_list()[:3]
    for dummy_user in dummy_line_users:
        line_user_repository.create(
            new_line_user=dummy_user,
        )

    # Act
    result = line_user_repository.delete()

    # Assert
    assert result == len(dummy_line_users)
    records_in_db = line_user_repository.find()
    assert len(records_in_db) == 0
