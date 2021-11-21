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
    query = {
        'user_name': target_users[0].user_name,
    }

    # Act
    result = user_repository.find(query=query)

    # Assert
    assert len(result) == len(target_users)
    for i in range(len(result)):
        assert isinstance(result[i], User)
        assert result[i].user_name == target_users[i].user_name
        assert result[i].line_user_name == target_users[i].line_user_name
        assert result[i].line_user_id == target_users[i].line_user_id
