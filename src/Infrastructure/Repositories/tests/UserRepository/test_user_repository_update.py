from src.Infrastructure.Repositories.UserRepository import UserRepository
from src.tests.dummies import generate_dummy_user_list


def test_success():
    # Arrange
    user_repository = UserRepository()
    dummy_users = generate_dummy_user_list()[:3]
    for dummy_user in dummy_users:
        result = user_repository.create(
            new_user=dummy_user
        )
    target_user = dummy_users[0]
    query = {
        'user_name': target_user.user_name,
    }
    new_values = {
        'line_user_id': 'updated'
    }

    # Act
    result = user_repository.update(
        query=query,
        new_values=new_values,
    )

    # Assert
    assert result == 1
    records_in_db = user_repository.find(query=query)
    for record in records_in_db:
        assert record.user_name == target_user.user_name
        assert record.line_user_name == target_user.line_user_name
        assert record.line_user_id == new_values['line_user_id']
