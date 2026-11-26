from html.parser import HTMLParser
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

import pytest
from authlib.integrations.flask_client import OAuth

from src import app
from src.Domains.Entities.WebUser import WebUser
from src.routes.web import auth


class Links(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.authorization_url = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and attrs.get('id') == 'line-login-button':
            self.authorization_url = attrs['href']


@pytest.fixture
def login_web(monkeypatch):
    monkeypatch.setattr(auth.config, 'IS_DEVELOPMENT', False)
    monkeypatch.setitem(app.config, 'TESTING', True)
    extension_key = 'authlib.integrations.flask_client'
    previous = app.extensions.get(extension_key)
    registry = OAuth(app)
    remote = registry.register(
        name='line', client_id='test-channel', client_secret='test-secret',
        authorize_url='https://access.line.me/oauth2/v2.1/authorize',
        access_token_url='https://api.line.me/oauth2/v2.1/token',
        api_base_url='https://api.line.me/', client_kwargs={'scope':'profile'},
    )
    remote.fetch_access_token = Mock(return_value={'access_token':'fake-access-token','token_type':'Bearer'})
    remote.get = Mock(return_value=SimpleNamespace(json=lambda:{'userId':'test-line-user','displayName':'Test User'}))
    monkeypatch.setattr(auth.oauth, 'create_client', lambda name: remote)
    repository = Mock()
    repository.find.return_value = [WebUser(_id='test-owner',web_user_name='Test User',
                                           linked_line_user_id='test-line-user',is_linked_line_user=True)]
    monkeypatch.setattr(auth, 'web_user_repository', repository)
    with app.test_client() as client:
        yield client, remote, repository
    if previous is None:
        app.extensions.pop(extension_key,None)
    else:
        app.extensions[extension_key] = previous


def authorization(client, path='/line/login?next=%2Fartists'):
    response = client.get(path)
    assert response.status_code == 200
    href = Links(response.get_data(as_text=True)).authorization_url
    assert href
    return response, parse_qs(urlsplit(href).query)


def test_protected_page_stops_at_login_screen_instead_of_automatically_opening_line(login_web):
    client, remote, repository = login_web
    response = client.get('/artists',follow_redirects=True)
    assert response.status_code == 200
    assert 'Location' not in response.headers
    assert 'LINEアプリでログイン' in response.get_data(as_text=True)
    remote.fetch_access_token.assert_not_called()
    repository.find.assert_not_called()


def test_direct_line_link_keeps_authlib_state_and_callback_and_is_not_cached(login_web):
    client, _, _ = login_web
    response, query = authorization(client)
    assert query['client_id'] == ['test-channel']
    assert urlsplit(query['redirect_uri'][0]).path == '/line/authorize'
    assert query['response_type'] == ['code'] and query['scope'] == ['profile']
    assert 'disable_auto_login' not in query
    state = query['state'][0]
    with client.session_transaction() as session:
        assert session['next_page_url'] == '/artists'
        assert session[f'_state_line_{state}']['data']['redirect_uri'] == query['redirect_uri'][0]
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.headers['Referrer-Policy'] == 'no-referrer'
    assert 'http-equiv="refresh"' not in response.get_data(as_text=True).lower()


def test_explicit_fallback_disables_auto_login_but_retains_state(login_web):
    client, _, _ = login_web
    _, query = authorization(client,'/line/login?mode=web&next=%2Fartists')
    assert query['disable_auto_login'] == ['true']
    assert query['state']
    assert query['redirect_uri'][0].endswith('/line/authorize')


def test_valid_callback_returns_to_original_page_and_consumes_state(login_web):
    client, remote, repository = login_web
    _, query = authorization(client)
    state = query['state'][0]
    response = client.get('/line/authorize',query_string={'state':state,'code':'test-code'})
    assert response.status_code == 302 and response.headers['Location'] == '/artists'
    remote.fetch_access_token.assert_called_once()
    repository.find.assert_called_once_with({'linked_line_user_id':'test-line-user'})
    with client.session_transaction() as session:
        assert session['login_user']['_id'] == 'test-owner'
        assert f'_state_line_{state}' not in session
    replay = client.get('/line/authorize',query_string={'state':state,'code':'test-code'})
    assert replay.status_code == 302
    assert remote.fetch_access_token.call_count == 1
    assert repository.find.call_count == 1


@pytest.mark.parametrize('invalid_state', [None,'not-the-session-state'])
def test_missing_or_wrong_state_never_fetches_a_token_or_logs_in(login_web,invalid_state):
    client, remote, repository = login_web
    authorization(client)
    params = {'code':'untrusted-code'}
    if invalid_state:
        params['state'] = invalid_state
    response = client.get('/line/authorize',query_string=params)
    assert response.status_code == 302 and response.headers['Location'].endswith('/line/login')
    remote.fetch_access_token.assert_not_called()
    repository.find.assert_not_called()
    with client.session_transaction() as session:
        assert 'login_user' not in session


def test_existing_login_does_not_start_another_authorization(login_web):
    client, remote, _ = login_web
    with client.session_transaction() as session:
        session['login_user'] = {'_id':'test-owner','web_user_name':'Test User'}
    response = client.get('/line/login?next=%2Fartists')
    assert response.status_code == 302 and response.headers['Location'] == '/artists'
    remote.fetch_access_token.assert_not_called()


def test_external_next_url_stays_on_the_application(login_web):
    client, _, _ = login_web
    _, query = authorization(client,'/line/login?next=https%3A%2F%2Fother.example%2Fartists')
    response = client.get('/line/authorize',query_string={'state':query['state'][0],'code':'test-code'})
    assert response.headers['Location'] == '/artists'
