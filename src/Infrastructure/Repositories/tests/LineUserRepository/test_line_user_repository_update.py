from src.Infrastructure.Repositories.LineUserRepository import LineUserRepository
from src.tests.dummies import generate_dummy_line_user_list


def test_success():
    # Arrange
    line_user_repository = LineUserRepository()
    dummy_line_users = generate_dummy_line_user_list()[:3]
    for dummy_line_user in dummy_line_users:
        result = line_user_repository.create(
            new_line_user=dummy_line_user
        )
    target_line_user = dummy_line_users[0]
    query = {
        'line_user_name': target_line_user.line_user_name,
    }
    new_values = {
        'line_user_id': 'updated'
    }

    # Act
    result = line_user_repository.update(
        query=query,
        new_values=new_values,
    )

    # Assert
    assert result == 1
    records_in_db = line_user_repository.find(query=query)
    for record in records_in_db:
        assert record.line_user_name == target_line_user.line_user_name
        assert record.line_user_id == new_values['line_user_id']
