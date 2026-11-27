import importlib
import re
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from threading import RLock
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

import pytest
from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.flask_client import OAuth
from authlib.oauth2.rfc7636 import create_s256_code_challenge

from src import app
from src.Domains.Entities.WebUser import WebUser
from src.routes.web import auth, line_handoff
from src.services.LineLoginHandoff import MAX_ATTEMPTS, LineLoginHandoff

module = importlib.import_module('src.services.LineLoginHandoff')
NOW = datetime(2026, 11, 27, tzinfo=timezone.utc)


class MemoryStore:
    """Firestore transaction double shared by repository instances."""
    def __init__(self):
        self.records = {}
        self.lock = RLock()

    def collection(self, name):
        return Collection(self)

    def transaction(self):
        return self

    def batch(self):
        return Batch()

    def set(self, ref, data):
        ref.create(data)

    def update(self, ref, values):
        self.records[ref.key].update(deepcopy(values))

    def delete(self, ref):
        ref.delete()


class Reference:
    def __init__(self, store, key):
        self.store, self.key = store, key

    def create(self, data, **kwargs):
        self.store.records[self.key] = deepcopy(data)

    def get(self, **kwargs):
        data = deepcopy(self.store.records.get(self.key))
        return SimpleNamespace(to_dict=lambda: data, reference=self)

    def delete(self, **kwargs):
        self.store.records.pop(self.key, None)


class Batch:
    def __init__(self):
        self.refs = []

    def delete(self, ref):
        self.refs.append(ref)

    def commit(self, **kwargs):
        assert kwargs == {'retry': None, 'timeout': 5}
        for ref in self.refs:
            ref.delete()


class Collection:
    def __init__(self, store):
        self.store = store

    def document(self, key):
        return Reference(self.store, key)

    def where(self, *, filter):
        assert filter.field_path == 'expires_at' and filter.op_string == '<='
        self.before = filter.value
        return self

    def limit(self, count):
        self.count = count
        return self

    def select(self, fields):
        return self

    def stream(self, **kwargs):
        keys = [key for key, data in self.store.records.items() if data['expires_at'] <= self.before]
        return (self.document(key).get() for key in keys[:self.count])


class Page(HTMLParser):
    def __init__(self, response):
        super().__init__(convert_charrefs=True)
        self.links, self.inputs = {}, {}
        self.html = response.get_data(as_text=True)
        self.feed(self.html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'id' in attrs:
            self.links[attrs['id']] = attrs['href']
        if tag == 'input' and 'name' in attrs:
            self.inputs[attrs['name']] = attrs.get('value', '')


@pytest.fixture
def setup(monkeypatch):
    store = MemoryStore()

    def transactional(function):
        def execute(tx):
            with tx.lock:
                return function(tx)
        return execute

    monkeypatch.setattr(module, 'firestore_client', store)
    monkeypatch.setattr(module.firestore, 'transactional', transactional)
    monkeypatch.setattr(module, 'now_utc', lambda: NOW)
    monkeypatch.setattr(auth.config, 'IS_DEVELOPMENT', False)
    monkeypatch.setitem(app.config, 'TESTING', True)
    monkeypatch.setitem(app.config, 'WTF_CSRF_ENABLED', True)
    previous = app.extensions.get('authlib.integrations.flask_client')
    remote = OAuth(app).register(
        name='line', client_id='test-channel', client_secret='fake-secret',
        authorize_url='https://access.line.me/oauth2/v2.1/authorize',
        access_token_url='https://api.line.me/oauth2/v2.1/token',
        api_base_url='https://api.line.me/', client_kwargs={'scope': 'profile'},
    )
    remote.fetch_access_token = Mock(return_value={'access_token': 'fake-line-token'})
    remote.get = Mock(return_value=SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {'userId': 'test-line-user', 'displayName': 'Test Name', 'pictureUrl': 'discard-me'},
    ))
    monkeypatch.setattr(auth.oauth, 'create_client', lambda _: remote)
    owners = Mock()
    owners.find.return_value = [WebUser(_id='test-owner', web_user_name='Test Name',
                                       linked_line_user_id='test-line-user', is_linked_line_user=True)]
    monkeypatch.setattr(auth, 'web_user_repository', owners)
    # Independent clients have separate cookie jars, as Home Screen and Safari do.
    yield SimpleNamespace(home=app.test_client(), safari=app.test_client(), other=app.test_client(),
                          remote=remote, owners=owners, store=store, repo=LineLoginHandoff())
    if previous is None:
        app.extensions.pop('authlib.integrations.flask_client', None)
    else:
        app.extensions['authlib.integrations.flask_client'] = previous


def start(env, mode=''):
    page = Page(env.home.get('/line/login?next=%2Fartists'))
    response = env.home.post('/line/handoff/start', data={'csrf_token': page.inputs['csrf_token'], 'mode': mode})
    assert response.status_code == 303
    waiting = Page(env.home.get(response.headers['Location']))
    query = parse_qs(urlsplit(waiting.links['line-handoff-button']).query)
    return query, waiting


def callback(env, query):
    return env.safari.get('/line/authorize', query_string={'state': query['state'][0], 'code': 'fake-code'})


def code_on(response):
    return re.search(r'id="handoff-code">([0-9]{8})<', response.get_data(as_text=True))[1]


def claim(client, csrf, code):
    return client.post('/line/handoff/claim', data={'csrf_token': csrf, 'confirmation_code': code})


def test_separate_cookie_callback_completes_only_in_original_home_app(setup):
    env = setup
    query, waiting = start(env)
    verifier = next(iter(env.store.records.values()))['verifier']
    assert query['code_challenge'] == [create_s256_code_challenge(verifier)]
    assert query['code_challenge_method'] == ['S256']
    response = callback(env, query)
    assert response.status_code == 200
    code = code_on(response)
    env.remote.fetch_access_token.assert_called_once_with(
        code='fake-code', redirect_uri=query['redirect_uri'][0], code_verifier=verifier, timeout=10)
    with env.safari.session_transaction() as session:
        assert 'login_user' not in session and 'access_token' not in session
    assert env.owners.find.call_count == 0
    document = next(iter(env.store.records.values()))
    assert 'verifier' not in document and 'fake-line-token' not in repr(document) and code not in repr(document)
    assert document['profile'] == {'userId': 'test-line-user', 'displayName': 'Test Name'}
    result = claim(env.home, waiting.inputs['csrf_token'], code)
    assert result.status_code == 302 and result.headers['Location'] == '/artists'
    with env.home.session_transaction() as session:
        assert session['login_user']['_id'] == 'test-owner'
        assert 'line_handoff' not in session and 'access_token' not in session
    assert env.store.records == {}
    env.owners.find.assert_called_once_with({'linked_line_user_id': 'test-line-user'})
    claim(env.home, waiting.inputs['csrf_token'], code)
    assert env.owners.find.call_count == 1


def test_new_user_registration_runs_only_in_originating_app(setup):
    env = setup
    env.owners.find.return_value = []
    query, waiting = start(env)
    code = code_on(callback(env, query))
    response = claim(env.home, waiting.inputs['csrf_token'], code)
    assert response.headers['Location'] == '/line/register'
    with env.home.session_transaction() as session:
        assert session['pending_line_user']['line_user_id'] == 'test-line-user'
    with env.safari.session_transaction() as session:
        assert 'pending_line_user' not in session


def test_callback_replay_does_not_exchange_or_replace_confirmation_code(setup):
    query, _ = start(setup)
    callback(setup, query)
    previous = deepcopy(setup.store.records)
    assert 'handoff-code' not in callback(setup, query).get_data(as_text=True)
    assert setup.remote.fetch_access_token.call_count == 1 and setup.store.records == previous


@pytest.mark.parametrize('state', ['h1.wrong', 'h1.' + 'x' * 43, 'h1./../bad'])
def test_unknown_or_malformed_state_fails_before_token_exchange(setup, state):
    start(setup)
    response = setup.safari.get('/line/authorize', query_string={'state': state, 'code': 'fake-code'})
    assert 'handoff-code' not in response.get_data(as_text=True)
    setup.remote.fetch_access_token.assert_not_called()


def test_number_alone_or_state_alone_cannot_log_in_a_different_browser(setup):
    query, waiting = start(setup)
    code = code_on(callback(setup, query))
    csrf = Page(setup.other.get('/line/login')).inputs['csrf_token']
    claim(setup.other, csrf, code)
    with setup.other.session_transaction() as session:
        session['line_handoff'] = {'state': query['state'][0], 'secret': 'wrong-secret'}
    claim(setup.other, csrf, code)
    with setup.other.session_transaction() as session:
        assert 'login_user' not in session
    assert claim(setup.home, waiting.inputs['csrf_token'], code).status_code == 302


def test_five_wrong_numbers_revoke_request_and_correct_number_cannot_be_used(setup):
    query, waiting = start(setup)
    code = code_on(callback(setup, query))
    wrong = '00000000' if code != '00000000' else '11111111'
    for _ in range(MAX_ATTEMPTS):
        claim(setup.home, waiting.inputs['csrf_token'], wrong)
    assert setup.store.records == {}
    claim(setup.home, waiting.inputs['csrf_token'], code)
    setup.owners.find.assert_not_called()


@pytest.mark.parametrize('step', ['callback', 'claim'])
def test_expiration_is_checked_even_when_background_cleanup_has_not_run(setup, monkeypatch, step):
    query, waiting = start(setup)
    code = code_on(callback(setup, query)) if step == 'claim' else '12345678'
    monkeypatch.setattr(module, 'now_utc', lambda: NOW + timedelta(minutes=5))
    if step == 'callback':
        callback(setup, query)
        setup.remote.fetch_access_token.assert_not_called()
    claim(setup.home, waiting.inputs['csrf_token'], code)
    setup.owners.find.assert_not_called()
    assert setup.store.records == {}


def test_start_and_claim_require_matching_csrf_and_resume_is_a_get(setup):
    assert setup.home.post('/line/handoff/start').status_code == 400
    query, _ = start(setup)
    assert parse_qs(urlsplit(Page(setup.home.get('/line/handoff')).links['line-handoff-button']).query)['state'] == query['state']
    code = code_on(callback(setup, query))
    assert setup.home.post('/line/handoff/claim', data={'confirmation_code': code}).status_code == 400
    assert setup.home.post('/line/handoff/claim', data={'csrf_token': 'wrong', 'confirmation_code': code}).status_code == 400
    setup.owners.find.assert_not_called()


def test_restart_revokes_old_flow_and_web_fallback_keeps_pkce(setup):
    old, _ = start(setup)
    new, _ = start(setup, 'web')
    assert new['disable_auto_login'] == ['true'] and new['code_challenge_method'] == ['S256']
    callback(setup, old)
    setup.remote.fetch_access_token.assert_not_called()
    assert len(setup.store.records) == 1
    assert code_on(callback(setup, new))


def test_cancelled_or_failed_exchange_cannot_later_be_claimed(setup):
    query, _ = start(setup)
    setup.remote.fetch_access_token.side_effect = OAuthError(error='invalid_grant')
    assert 'handoff-code' not in callback(setup, query).get_data(as_text=True)
    assert setup.store.records == {}
    setup.owners.find.assert_not_called()


def test_concurrent_consumption_by_different_instances_happens_once(setup):
    query, _ = start(setup)
    code = code_on(callback(setup, query))
    with setup.home.session_transaction() as session:
        pending = dict(session['line_handoff'])

    def consume(_):
        with app.app_context():
            return LineLoginHandoff().consume(pending['state'], pending['secret'], code)[0]

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(consume, range(20)))
    assert results.count('ok') == 1 and setup.store.records == {}


def test_expired_record_cleanup_is_bounded_and_does_not_touch_active_requests(setup, monkeypatch):
    for _ in range(25):
        start(setup)
        setup.home = app.test_client()
    monkeypatch.setattr(module, 'now_utc', lambda: NOW + timedelta(minutes=6))
    start(setup)
    assert len(setup.store.records) == 6


def test_pages_do_not_cache_or_send_secrets_as_referrer(setup):
    query, _ = start(setup)
    for response in (setup.home.get('/line/handoff'), callback(setup, query)):
        assert response.headers['Cache-Control'] == 'no-store'
        assert response.headers['Referrer-Policy'] == 'no-referrer'
        assert response.headers['X-Frame-Options'] == 'DENY'


def test_concurrent_callbacks_can_exchange_a_state_only_once(setup):
    query, _ = start(setup)

    def begin(_):
        return LineLoginHandoff().begin_callback(query['state'][0])

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(begin, range(20)))
    assert sum(result is not None for result in results) == 1


@pytest.mark.parametrize('response_type', ['cancel', 'missing_code', 'missing_identity'])
def test_invalid_provider_responses_do_not_leave_a_claimable_login(setup, response_type):
    query, _ = start(setup)
    args = {'state': query['state'][0], 'code': 'fake-code'}
    if response_type == 'cancel':
        args = {'state': query['state'][0], 'error': 'access_denied'}
    elif response_type == 'missing_code':
        args = {'state': query['state'][0]}
    else:
        setup.remote.get.return_value.json = lambda: {'displayName': 'No identity'}
    response = setup.safari.get('/line/authorize', query_string=args)
    assert 'handoff-code' not in response.get_data(as_text=True)
    assert setup.store.records == {}
    setup.owners.find.assert_not_called()


def test_number_from_another_request_cannot_sign_in_this_browser(setup):
    first, waiting = start(setup)
    first_code = code_on(callback(setup, first))
    original = setup.home
    setup.home = app.test_client()
    second, _ = start(setup)
    second_code = code_on(callback(setup, second))
    # A random collision is valid for both independently, so choose a guaranteed wrong value.
    if second_code == first_code:
        second_code = '00000000' if first_code != '00000000' else '11111111'
    assert claim(original, waiting.inputs['csrf_token'], second_code).status_code == 303
    setup.owners.find.assert_not_called()
    assert claim(original, waiting.inputs['csrf_token'], first_code).status_code == 302


def test_existing_account_session_is_not_switched_by_an_old_pending_handoff(setup):
    query, waiting = start(setup)
    code = code_on(callback(setup, query))
    with setup.home.session_transaction() as session:
        session['login_user'] = {'_id': 'already-authenticated-owner', 'web_user_name': 'Existing'}
    claim(setup.home, waiting.inputs['csrf_token'], code)
    with setup.home.session_transaction() as session:
        assert session['login_user']['_id'] == 'already-authenticated-owner'
    assert setup.store.records == {}
    setup.owners.find.assert_not_called()


def test_callback_in_original_app_can_complete_without_switching_browsers(setup):
    query, _ = start(setup)
    response = setup.home.get('/line/authorize', query_string={'state': query['state'][0], 'code': 'fake-code'})
    page = Page(response)
    assert page.inputs['confirmation_code'] == code_on(response)
    assert claim(setup.home, page.inputs['csrf_token'], page.inputs['confirmation_code']).status_code == 302
    setup.owners.find.assert_called_once()


def test_app_relaunch_can_resume_pending_code_entry_and_stale_identity_is_cleared(setup):
    query, _ = start(setup)
    code = code_on(callback(setup, query))
    page = Page(setup.home.get('/line/login'))
    assert '開始済みのログインを続ける' in page.html
    # A resumed GET does not need the original authorization link anymore.
    resumed = Page(setup.home.get('/line/handoff'))
    assert 'line-handoff-button' not in resumed.links
    with setup.home.session_transaction() as session:
        session['access_token'] = 'old-unrelated-token'
        session['id_token'] = 'old-unrelated-id-token'
        session['pending_line_user'] = {'line_user_id': 'old-pending-identity'}
    assert claim(setup.home, resumed.inputs['csrf_token'], code).status_code == 302
    with setup.home.session_transaction() as session:
        assert 'access_token' not in session and 'id_token' not in session and 'pending_line_user' not in session


def test_optional_cleanup_timeout_does_not_prevent_a_new_login(setup, monkeypatch):
    from google.api_core.exceptions import DeadlineExceeded

    monkeypatch.setattr(line_handoff.handoffs, 'cleanup', Mock(side_effect=DeadlineExceeded('cleanup unavailable')))
    query, _ = start(setup)
    assert code_on(callback(setup, query))
