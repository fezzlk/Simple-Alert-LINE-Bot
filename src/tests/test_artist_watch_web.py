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
    cache = Mock()
    cache.index.return_value = {}
    monkeypatch.setattr(artists, "artist_source_cache_repository", cache)
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


def test_source_plan_is_visible_before_first_record_without_custom_urls(web):
    client, repository = web
    repository.list_for_owner.return_value = [ArtistWatch("A1", "W1", "Chris Dave", ["クリス・デイヴ"])]
    text = client.get("/artists").get_data(as_text=True)
    assert 'href="https://www.billboard-live.com/tokyo/schedules"' in text
    assert 'href="https://www.billboard-live.com/yokohama/schedules"' in text
    assert "検索語（次回予定）" in text
    assert "来日 OR 公演 OR ライブ" in text
    assert "次回の巡回後に表示されます" in text


def test_last_scan_shows_individual_pages_failures_and_queries(web):
    client, repository = web
    repository.list_for_owner.return_value = [ArtistWatch(
        "A1", "W1", "Chris Dave", last_page_checks=[
            {"url": "https://example.com/show", "title": "Chris Dave live", "kind": "linked", "status": "ok", "event_count": 1},
            {"url": "https://example.com/blocked", "title": "Blocked", "kind": "search", "status": "error", "reason": "HTTP 403"},
        ], last_search_checks=[{"query": '"Chris Dave" Tokyo live', "status": "ok"}], last_skipped_details=3,
    )]
    text = client.get("/artists").get_data(as_text=True)
    assert 'href="https://example.com/show"' in text
    assert "公式ページから発見" in text
    assert "Web検索から発見" in text
    assert "公演情報 1件" in text
    assert "取得できず" in text
    assert "HTTP 403" in text
    assert "前回のWeb検索" in text
    assert "3件" in text


def test_stored_invalid_history_url_is_never_rendered_as_a_link(web):
    client, repository = web
    repository.list_for_owner.return_value = [ArtistWatch("A1", "W1", "Chris Dave", last_page_checks=[
        {"url": "javascript:alert(1)", "title": "<script>bad</script>", "kind": "search", "status": "error"},
    ])]
    text = client.get("/artists").get_data(as_text=True)
    assert 'href="javascript:' not in text
    assert "<script>bad</script>" not in text
    assert "&lt;script&gt;bad&lt;/script&gt;" in text


def test_prefecture_inventory_shows_shared_fetch_results_without_loading_bodies(web):
    from datetime import datetime, timezone
    client, _ = web
    artists.artist_source_cache_repository.index.return_value = {
        'https://cortez.jp/':{'status':'partial','checked_at':datetime.now(timezone.utc),'page_count':1,
                              'reason':'埋め込みの予定表は未確認',
                              'page_checks':[{'url':'https://cortez.jp/schedule/','title':'公演予定','status':'ok'}]},
    }
    text = client.get('/artists').get_data(as_text=True)
    assert '関東1都6県' in text and '茨城（' in text and '栃木（' in text and '群馬（' in text
    assert 'フェス' in text and '大型会場' in text
    assert '一部取得' in text and '埋め込みの予定表は未確認' in text
    assert 'href="https://cortez.jp/schedule/"' in text
    artists.artist_source_cache_repository.index.assert_called_once_with(include_text=False)


def test_nested_cached_page_link_is_sanitized(web):
    client, repository = web
    repository.list_for_owner.return_value = [ArtistWatch('a','W1','Artist',last_page_checks=[
        {'url':'https://example.com/','status':'ok','kind':'shared','title':'Source',
         'pages':[{'url':'javascript:alert(1)','title':'<script>x</script>','status':'ok'}]},
    ])]
    text = client.get('/artists').get_data(as_text=True)
    assert 'href="javascript:' not in text and '<script>x</script>' not in text
