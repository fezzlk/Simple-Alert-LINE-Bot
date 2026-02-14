import pytest
from flask import Flask
from src.routes.web.habit import views_blueprint

@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = 'test'
    app.register_blueprint(views_blueprint)
    return app

def test_habit_task_log_calendar_toggle(client, app):
    # Simulate login and minimal session
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['login_name'] = 'testuser'
            sess['login_email'] = 'test@example.com'
            sess['user_id'] = 'dummyid'
        # Assume a dummy task_id exists, or mock the repository if needed
        response = client.get('/habit/dummyid')
        html = response.get_data(as_text=True)
        assert 'toggle-view-btn' in html
        assert 'calendar-view' in html
        assert 'カレンダー表示に切替' in html
