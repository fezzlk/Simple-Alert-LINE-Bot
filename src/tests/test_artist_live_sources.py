import json
import socket
import time
from datetime import date

import pytest

from src.Domains.Entities.ArtistWatch import ArtistWatch, ConcertEvent, matches_artist
from src.services.ArtistLiveSourceService import (
    ArtistLiveSourceService,
    ConcertHTML,
    SourceError,
    _PinnedHTTPSConnection,
    extract_events,
    validate_source_url,
)

WATCH = ArtistWatch("watch", "owner", "Chris Dave", ["クリス・デイヴ"])
SHOW_URL = "https://www.billboard-live.com/tokyo/show?event_id=ev-test"
SHOW = """<main><h1>TOKYO</h1><p>2026.11.19 (Thu)</p>
<h1>Chris Dave, MonoNeon and Justus West</h1><p>クリス・デイヴ</p>
<h2>Overview</h2><p>Adele and D'Angelo have worked with Chris Dave.</p>
<h2>Member</h2><p>Chris Dave（Dr） MonoNeon（Ba）</p>
<h2>Open / Start</h2><p>1st 17:30 / 2nd 20:30</p>
<h2>Notice</h2><h2>Tour Information</h2>
<p>11/15 LOVE SUPREME ※公演キャンセル</p><p>11/20 Billboard Live OSAKA</p>
<h2>Recommended Shows</h2><p>2026.12.20 Other Artist</p></main>"""


def test_chris_dave_joint_bill_excludes_recommendations_and_other_cancelled_festival():
    events = extract_events(ConcertHTML(SHOW), SHOW_URL, WATCH, date(2026, 10, 1))
    assert len(events) == 1
    assert events[0].event_date == date(2026, 11, 19)
    assert events[0].venue == "Billboard Live TOKYO"
    assert events[0].status == "scheduled"


def test_past_show_is_not_notified():
    assert extract_events(ConcertHTML(SHOW), SHOW_URL, WATCH, date(2026, 11, 22)) == []


def test_osaka_show_with_tokyo_in_footer_is_not_notified():
    assert extract_events(ConcertHTML(SHOW), SHOW_URL.replace("tokyo", "osaka"), WATCH, date(2026, 10, 1)) == []


def test_artist_only_mentioned_in_biography_is_not_a_performer():
    adele = ArtistWatch("adele", "owner", "Adele")
    assert extract_events(ConcertHTML(SHOW), SHOW_URL, adele, date(2026, 10, 1)) == []


def test_blue_note_contiguous_dates_do_not_include_other_artists_navigation():
    html = '''<h2>BEN WENDEL : BaRcoDe</h2><p class="date">2027 3.21 sun., 3.22 mon., 3.23 tue.</p>
    <p>Biography mentions Chris Dave, but he does not perform.</p>
    <table><tr><td>Ben Wendel(sax)</td><td>Joel Ross(mar)</td></tr></table>
    <div id="ticketPanelTop">【一般】11.21 sat. 12:00pm〜</div>
    <span id="pageNaviPrevInformationDate">2027 3.6 sat., 3.7 sun.</span><h4>Other Artist</h4>'''
    watch = ArtistWatch("ben", "owner", "Ben Wendel")
    url = "https://www.bluenote.co.jp/jp/artists/ben-wendel/"
    events = extract_events(ConcertHTML(html), url, watch, date(2026, 11, 22))
    assert [event.event_date for event in events] == [date(2027, 3, day) for day in (21, 22, 23)]
    assert all("11.21" in event.ticket_info for event in events)
    assert extract_events(ConcertHTML(html), url, WATCH, date(2026, 11, 22)) == []
    guest = ArtistWatch("joel", "owner", "Joel Ross")
    assert len(extract_events(ConcertHTML(html), url, guest, date(2026, 11, 22))) == 3


def test_cotton_club_multiple_months_and_band_member():
    html = '''<h1>PLATINA JAZZ</h1><div class="artist_date">2026 11.29 sun., 11.30 mon., 12.1 tue., 12.2 wed.</div>
    <h4>MEMBER</h4><p>Ola Bothzén (ds) Rasmus Faber (vib)</p>
    <h4>＜予約受付開始日＞</h4><p>【一般WEB】予約開始日：9.14 mon. 12:00pm〜</p><h4>CHARGE</h4>'''
    watch = ArtistWatch("rasmus", "owner", "Rasmus Faber")
    events = extract_events(ConcertHTML(html), "https://www.cottonclubjapan.co.jp/jp/sp/artists/platina-jazz-261129/",
                            watch, date(2026, 11, 22))
    assert [event.event_date for event in events] == [date(2026, 11, 29), date(2026, 11, 30), date(2026, 12, 1), date(2026, 12, 2)]


def test_performer_member_matches_even_if_band_title_omits_artist():
    show = SHOW.replace("Chris Dave, MonoNeon and Justus West", "The Drumhedz Session").replace("<p>クリス・デイヴ</p>", "")
    events = extract_events(ConcertHTML(show), SHOW_URL, WATCH, date(2026, 10, 1))
    assert len(events) == 1
    assert events[0].title == "The Drumhedz Session"


def test_structured_event_uses_performer_and_explicit_location_not_footer():
    item = {"@type": "MusicEvent", "name": "Special Band", "startDate": "2027-01-08T19:00:00+09:00",
            "performer": [{"name": "Chris Dave"}],
            "location": {"name": "Blue Note Tokyo", "address": {"addressRegion": "東京都"}},
            "offers": {"validFrom": "2026-12-01T12:00:00+09:00"}}
    html = '<script type="application/ld+json">' + json.dumps({"@graph": [item]}) + '</script>'
    events = extract_events(ConcertHTML(html), "https://example.com/show", WATCH, date(2026, 11, 22))
    assert len(events) == 1
    assert events[0].ticket_info == "2026-12-01T12:00:00+09:00"
    item["location"] = {"name": "Osaka Hall", "address": "大阪府"}
    html = '<script type="application/ld+json">' + json.dumps(item) + '</script><footer>Tokyo</footer>'
    assert extract_events(ConcertHTML(html), "https://example.com/show", WATCH, date(2026, 11, 22)) == []


def test_generic_promoter_requires_same_event_date_location_and_venue():
    html = '<main><h1>Chris Dave Japan Tour</h1><p>2027.1.8 東京 会場: Blue Note Tokyo 開演19:00</p></main>'
    events = extract_events(ConcertHTML(html), "https://example.com/tour", WATCH, date(2026, 11, 22))
    assert len(events) == 1
    assert events[0].venue == "Blue Note Tokyo"


def test_nationwide_tour_cannot_assign_osaka_date_to_tokyo_venue():
    html = '''<main><h1>Chris Dave Japan Tour</h1><article>
    <p>2027.1.8 東京 会場: LIQUIDROOM 開演19:00</p>
    <p>2027.1.10 大阪 会場: Osaka Hall 開演19:00</p>
    </article></main>'''
    events = extract_events(ConcertHTML(html), "https://example.com/tour", WATCH, date(2026, 11, 22))
    assert [(event.event_date, event.venue) for event in events] == [(date(2027, 1, 8), "LIQUIDROOM")]


def test_identity_unifies_language_variants_without_title_or_tracking_url():
    event = ConcertEvent("New headline", date(2027, 1, 8), "Billboard Live TOKYO", SHOW_URL)
    same = ConcertEvent("Different title", date(2027, 1, 8), "ビルボードライブ東京", SHOW_URL + "&utm_source=news")
    assert event.key("Chris Dave") == same.key("Chris Dave")
    assert event.fingerprint == same.fingerprint
    assert event.fingerprint != ConcertEvent(**{**event.__dict__, "status": "cancelled"}).fingerprint


def test_name_boundaries_and_unicode():
    assert matches_artist("Chris Dave（Dr）", WATCH.names)
    assert matches_artist("クリス・デイヴ、来日", WATCH.names)
    assert not matches_artist("Chris Davenport concert", WATCH.names)


@pytest.mark.parametrize("url", ["http://example.com", "https://localhost/", "https://127.0.0.1/",
                                 "https://[::1]/", "https://169.254.169.254/", "https://example.com:8080/",
                                 "https://user:secret@example.com/", "file:///etc/passwd"])
def test_unsafe_source_urls_rejected(url):
    with pytest.raises(ValueError):
        validate_source_url(url)


def test_private_dns_never_opens_a_socket(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 443))])
    monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: pytest.fail("private socket opened"))
    with pytest.raises(SourceError, match="non_public_address"):
        _PinnedHTTPSConnection("public-looking.example.com").connect()


def test_exhausted_search_budget_still_crawls_official_sources():
    class Client:
        def __init__(self, deadline):
            pass

        def html(self, url):
            return (SHOW, SHOW_URL) if "billboard-live.com/tokyo" in url else ("<main></main>", url)

        def search(self, *args):
            pytest.fail("Search must stop before sending HTTP")

    result = ArtistLiveSourceService("test-key", Client).discover(
        WATCH, date(2026, 10, 1), lambda: False, time.monotonic() + 10
    )
    assert result.checked_pages > 0
    assert len(result.events) == 1
    assert any("上限" in warning for warning in result.warnings)


def test_source_failure_is_visible_and_does_not_expose_upstream_secret():
    class Client:
        def __init__(self, deadline):
            pass

        def html(self, url):
            raise RuntimeError("X-Subscription-Token: secret-test-value")

    result = ArtistLiveSourceService(client_factory=Client).discover(
        WATCH, date(2026, 10, 1), lambda: True, time.monotonic() + 10
    )
    assert result.checked_pages == 0
    assert result.warnings
    assert "secret-test-value" not in str(result)
