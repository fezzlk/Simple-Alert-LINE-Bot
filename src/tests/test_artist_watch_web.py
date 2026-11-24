from unittest.mock import Mock

import pytest

from src import app, config
from src.Domains.Entities.ArtistWatch import ArtistWatch
from src.routes.web import artists


@pytest.fixture
def web(monkeypatch):
    repository = Mock()
    repository.list_for_owner.return_value = []
    repository.search_usage.return_value = 0
    monkeypatch.setattr(artists, "artist_watch_repository", repository)
    monkeypatch.setattr(config, "BRAVE_SEARCH_API_KEY", "")
    app.config.update(TESTING=True)
    with app.test_client() as client:
        with client.session_transaction() as session:
            session["login_user"] = {"_id": "W1", "web_user_name": "test", "is_linked_line_user": False}
        yield client, repository


def csrf(client):
    import re
    page = client.get("/artists").get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)


def test_mobile_ready_page_explains_line_link_and_search_setup(web):
    client, _ = web
    page = client.get("/artists")
    assert page.status_code == 200
    text = page.get_data(as_text=True)
    assert 'name="viewport"' in text
    assert "アーティストを追加" in text
    assert "Web横断検索は準備中" in text
    assert "LINE連携" in text


def test_save_uses_session_owner_and_preserves_aliases(web):
    client, repository = web
    response = client.post("/artists/save", data={"csrf_token": csrf(client), "artist_name": "Chris Dave",
                                                "owner_id": "W2", "aliases": "クリス・デイヴ\nChris Dave and the Drumhedz"})
    assert response.status_code == 302
    repository.save.assert_called_once_with("W1", "Chris Dave", ["クリス・デイヴ", "Chris Dave and the Drumhedz"], [], "")


def test_missing_csrf_is_rejected(web):
    client, repository = web
    assert client.post("/artists/save", data={"artist_name": "Chris Dave"}).status_code == 400
    repository.save.assert_not_called()


def test_invalid_custom_url_is_not_persisted(web):
    client, repository = web
    response = client.post("/artists/save", data={"csrf_token": csrf(client), "artist_name": "Chris Dave",
                                                "source_urls": "https://169.254.169.254/"})
    assert response.status_code == 302
    repository.save.assert_not_called()


def test_non_owner_edit_returns_404(web):
    client, repository = web
    repository.save.side_effect = LookupError
    response = client.post("/artists/save", data={"csrf_token": csrf(client), "watch_id": "other-owner-watch",
                                                "artist_name": "Chris Dave"})
    assert response.status_code == 404


def test_artist_name_is_escaped_and_edit_form_is_prefilled(web):
    client, repository = web
    repository.list_for_owner.return_value = [ArtistWatch("A1", "W1", '<script>alert(1)</script>', ["クリス・デイヴ"])]
    text = client.get("/artists").get_data(as_text=True)
    assert '<script>alert(1)</script>' not in text
    assert '&lt;script&gt;' in text
    assert "クリス・デイヴ" in text


def test_artist_routes_require_login(web):
    client, repository = web
    with client.session_transaction() as session:
        session.clear()
    assert client.get("/artists").status_code == 302
    repository.list_for_owner.assert_not_called()
