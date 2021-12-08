from src.Infrastructure.Repositories.WebUserRepository import WebUserRepository
from src.tests.dummies import generate_dummy_web_user_list


def test_success():
    # Arrange
    web_user_repository = WebUserRepository()
    dummy_web_users = generate_dummy_web_user_list()[:3]
    for dummy_web_user in dummy_web_users:
        result = web_user_repository.create(
            new_web_user=dummy_web_user
        )
    target_web_user = dummy_web_users[0]
    query = {
        'web_user_name': target_web_user.web_user_name,
    }
    new_values = {
        'web_user_email': 'updated'
    }

    # Act
    result = web_user_repository.update(
        query=query,
        new_values=new_values,
    )

    # Assert
    assert result == 1
    records_in_db = web_user_repository.find(query=query)
    for record in records_in_db:
        assert record.web_user_name == target_web_user.web_user_name
        assert record.web_user_email == new_values['web_user_email']
