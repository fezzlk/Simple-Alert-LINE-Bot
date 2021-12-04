from src.Domains.Entities.LineUser import LineUser
from src.Infrastructure.Repositories.LineUserRepository import LineUserRepository
from src.tests.dummies import generate_dummy_line_user_list


def test_success():
    # Arrange
    line_user_repository = LineUserRepository()
    dummy_line_users = generate_dummy_line_user_list()[:3]
    for dummy_line_user in dummy_line_users:
        line_user_repository.create(
            new_line_user=dummy_line_user,
        )
    target_line_users = dummy_line_users[:1]
    query = {
        'line_user_id': target_line_users[0].line_user_id,
    }

    # Act
    result = line_user_repository.find(query=query)

    # Assert
    assert len(result) == len(target_line_users)
    for i in range(len(result)):
        assert isinstance(result[i], LineUser)
        assert result[i].line_user_name == target_line_users[i].line_user_name
        assert result[i].line_user_id == target_line_users[i].line_user_id


def test_success_hit_all_records():
    # Arrange
    line_user_repository = LineUserRepository()
    dummy_line_users = generate_dummy_line_user_list()[:3]
    for dummy_line_user in dummy_line_users:
        line_user_repository.create(
            new_line_user=dummy_line_user,
        )

    # Act
    result = line_user_repository.find()

    # Assert
    assert len(result) == len(dummy_line_users)
    for i in range(len(result)):
        assert isinstance(result[i], LineUser)
        assert result[i].line_user_name == dummy_line_users[i].line_user_name
        assert result[i].line_user_id == dummy_line_users[i].line_user_id
