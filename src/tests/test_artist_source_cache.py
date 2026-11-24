import importlib
import json
import time
import zlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.Domains.ArtistSourceCatalog import PREFECTURES, SOURCES, source_id, unpack_cache, venue_for_url
from src.Domains.Entities.ArtistWatch import ArtistWatch
from src.Infrastructure.Repositories.ArtistSourceCacheRepository import ArtistSourceCacheRepository
from src.services.ArtistLiveSourceService import ArtistLiveSourceService, ConcertHTML, extract_events
from src.tests.test_artist_watch_repository import Database
from src.UseCases.Line.RefreshArtistSourcesUseCase import RefreshArtistSourcesUseCase, schedule_links

NOW = datetime(2026, 11, 24, 3, tzinfo=timezone.utc)
SOURCE = next(source for source in SOURCES if source['url'] == 'https://cortez.jp/')
WATCH = ArtistWatch('watch-private', 'owner-private', 'Test Artist')
HTML = '<main><article><h2>Test Artist live</h2><p>2026年12月13日 OPEN 16:30 START 17:00</p></article></main>'


@pytest.fixture
def cache_db(monkeypatch):
    module = importlib.import_module('src.Infrastructure.Repositories.ArtistSourceCacheRepository')
    db = Database()
    def transactional(function):
        def run(tx):
            with tx.lock:
                return function(tx)
        return run
    monkeypatch.setattr(module, 'firestore_client', db)
    monkeypatch.setattr(module.firestore, 'transactional', transactional)
    return db


def test_daily_cursor_is_atomic_and_finishes_once_per_day(cache_db):
    repo = ArtistSourceCacheRepository()
    with ThreadPoolExecutor(max_workers=8) as pool:
        claimed = list(pool.map(lambda _: repo.claim_next([SOURCE], NOW), range(16)))
    assert len([item for item in claimed if item]) == 1
    source, token = next(item for item in claimed if item)
    repo.finish(source, 'wrong', {'status':'error'}, NOW)
    assert repo.index() == {}
    repo.finish(source, token, {'status':'ok','pages_z':b'body','text_z':b'index'}, NOW)
    assert 'pages_z' not in repo.index()[SOURCE['url']]
    assert repo.pages(SOURCE['url']) == b'body'
    assert repo.claim_next([SOURCE], NOW + timedelta(minutes=2)) is None
    assert repo.claim_next([SOURCE], NOW + timedelta(days=1))


def test_lost_worker_cannot_overwrite_new_claim(cache_db):
    repo = ArtistSourceCacheRepository()
    _, old_token = repo.claim_next([SOURCE], NOW)
    _, new_token = repo.claim_next([SOURCE], NOW + timedelta(minutes=1))
    repo.finish(SOURCE, old_token, {'status':'ok'}, NOW)
    assert repo.index() == {}
    repo.finish(SOURCE, new_token, {'status':'error'}, NOW)
    assert repo.index()[SOURCE['url']]['status'] == 'error'


def test_shared_refresh_is_reused_by_artists_without_refetching(cache_db, monkeypatch):
    class Client:
        calls = []
        def __init__(self, deadline): pass
        def html(self, url):
            self.calls.append(url)
            return HTML, url
    watches = Mock()
    watches.has_enabled.return_value = True
    repo = ArtistSourceCacheRepository()
    job = RefreshArtistSourcesUseCase(repo, watches, Client, [SOURCE])
    assert job.execute(NOW)['status'] == 'ok'
    assert job.execute(NOW + timedelta(minutes=1))['status'] == 'idle'
    assert Client.calls == [SOURCE['url']]
    module = importlib.import_module('src.services.ArtistLiveSourceService')
    monkeypatch.setattr(module, 'SOURCES', [SOURCE])
    # An artist scan must not fetch any standard source directly.
    client = Mock()
    client.html.side_effect = AssertionError('Unexpected standard HTTP fetch')
    service = ArtistLiveSourceService(client_factory=lambda _: client, cache_repository=repo)
    first = service.discover(WATCH, NOW.date(), lambda: False, time.monotonic()+18)
    second = service.discover(ArtistWatch('other-watch','other-owner','Other Artist'), NOW.date(), lambda: False, time.monotonic()+18)
    assert len(first.events) == 1
    assert first.events[0].venue == SOURCE['name']
    assert second.events == []
    client.html.assert_not_called()
    assert first.page_checks[0]['checked_at'] == NOW.isoformat()
    stored = cache_db.data[('artist_source_cache', source_id(SOURCE['url']))]
    assert 'owner-private' not in str(stored) and 'watch-private' not in str(stored)


def test_no_enabled_watch_does_not_crawl_or_claim():
    repo, watches = Mock(), Mock()
    watches.has_enabled.return_value = False
    client = Mock()
    assert RefreshArtistSourcesUseCase(repo, watches, client).execute(NOW)['status'] == 'idle'
    repo.claim_next.assert_not_called()
    client.assert_not_called()


@pytest.mark.parametrize('status,refreshes', [('idle',1),('ok',0),('watch_changed',0),('notification_pending',0)])
def test_minute_route_never_stacks_shared_fetch_on_artist_work(monkeypatch,status,refreshes):
    from src import app
    api = importlib.import_module('src.routes.api')
    stocks, artists, refresh = Mock(), Mock(), Mock()
    artists.return_value.execute.return_value = {'status':status}
    monkeypatch.setattr(api,'CheckExpiredStockUseCase',stocks)
    monkeypatch.setattr(api,'CheckArtistLiveUseCase',artists)
    monkeypatch.setattr(api,'RefreshArtistSourcesUseCase',refresh)
    with app.test_request_context('/_api/v1/check_expire',method='POST'):
        assert api.check_expire.__wrapped__() == 'done'
    stocks.return_value.execute.assert_called_once()
    assert refresh.call_count == refreshes


def test_upstream_exception_is_safe_and_old_body_is_not_retained(cache_db):
    repo = ArtistSourceCacheRepository()
    client, watches = Mock(), Mock()
    client.html.side_effect = RuntimeError('SECRET-TEST-VALUE')
    watches.has_enabled.return_value = True
    result = RefreshArtistSourcesUseCase(repo, watches, lambda _: client, [SOURCE]).execute(NOW)
    assert result['status'] == 'error'
    assert repo.pages(SOURCE['url']) is None
    assert 'SECRET-TEST-VALUE' not in str(repo.index())


def test_missing_and_old_cache_are_not_used_or_crawled_directly(monkeypatch):
    module = importlib.import_module('src.services.ArtistLiveSourceService')
    monkeypatch.setattr(module, 'SOURCES', [SOURCE])
    repo = Mock()
    repo.index.return_value = {SOURCE['url']:{'checked_at':NOW-timedelta(days=3), 'status':'ok'}}
    client = Mock()
    result = ArtistLiveSourceService(client_factory=lambda _: client, cache_repository=repo).discover(
        WATCH, NOW.date(), lambda: False, time.monotonic()+18)
    assert result.checked_pages == 0 and result.warnings
    assert result.page_checks[0]['status'] == 'stale'
    repo.pages.assert_not_called()
    client.html.assert_not_called()


def test_compression_has_a_hard_expansion_limit():
    assert unpack_cache(zlib.compress(b'ok'), 2) == 'ok'
    with pytest.raises(ValueError):
        unpack_cache(zlib.compress(b'x'*100_000), 100)


def test_structured_only_performer_is_included_in_the_cache_search_index(cache_db):
    repo, client, watches = ArtistSourceCacheRepository(), Mock(), Mock()
    event = {'@type':'MusicEvent','name':'Festival Band','performer':{'name':'Test Artist'},
             'location':{'name':'Cortez','address':'茨城県'},'startDate':'2026-12-13'}
    client.html.return_value = ('<script type="application/ld+json">'+json.dumps(event)+'</script>', SOURCE['url'])
    watches.has_enabled.return_value = True
    RefreshArtistSourcesUseCase(repo, watches, lambda _: client, [SOURCE]).execute(NOW)
    assert 'Test Artist' in unpack_cache(repo.index()[SOURCE['url']]['text_z'], 10000)


def test_enabled_check_observes_paused_watches(cache_db, monkeypatch):
    module = importlib.import_module('src.Infrastructure.Repositories.ArtistWatchRepository')
    monkeypatch.setattr(module, 'firestore_client', cache_db)
    watches = module.ArtistWatchRepository()
    assert not watches.has_enabled()
    ref = cache_db.collection('artist_watches').document('A1')
    ref.set({'enabled':False})
    assert not watches.has_enabled()
    ref.update({'enabled':True})
    assert watches.has_enabled()


def test_blue_note_place_member_is_detected_without_using_artist_biography():
    url = 'https://www.bluenoteplace.jp/live/test-show/'
    doc = ConcertHTML('<main>Title A Soul Journey Date &amp; Showtimes 2026 12.11 fri. ——— [1st] OPEN 18:00'
                      ' MEMBER Test Artist (drums) ARTIST INFORMATION Other Artist influenced by Biography Artist</main>')
    assert extract_events(doc, url, WATCH, NOW.date())[0].event_date.isoformat() == '2026-12-11'
    assert extract_events(doc, url, ArtistWatch('a','b','Biography Artist'), NOW.date()) == []


def test_calendar_year_month_never_comes_from_copyright_or_a_different_month():
    doc = ConcertHTML('<main><h2>2026年12月</h2><table><tr><td>13 Test Artist LIVE OPEN 17:00</td></tr></table></main>')
    assert extract_events(doc, SOURCE['url'], WATCH, NOW.date())[0].event_date.isoformat() == '2026-12-13'
    doc = ConcertHTML('<main><h2>2026年11月</h2><h2>2026年12月</h2><table><tr><td>13 Test Artist LIVE OPEN 17:00</td></tr></table></main>')
    assert extract_events(doc, SOURCE['url'], WATCH, NOW.date()) == []


def test_schedule_navigation_is_bounded_and_excludes_reservations_and_cross_host():
    document = ConcertHTML('<a href="/schedule/">SCHEDULE</a><a href="https://elsewhere.example/schedule">SCHEDULE</a>'
                           '<a href="/schedule/ticket">SCHEDULE</a><a href="/live-calendar/">live calendar</a>'
                           '<a href="/third-schedule/">schedule</a>')
    assert schedule_links(document, SOURCE['url']) == ['https://cortez.jp/schedule/','https://cortez.jp/live-calendar/']


def test_official_next_month_calendar_links_are_used_without_past_month_or_other_venue():
    doc = ConcertHTML('<a href="./?cal=202610"></a><a href="./?cal=202612"></a>')
    assert schedule_links(doc,'https://www.bluenoteplace.jp/live/',NOW.date()) == ['https://www.bluenoteplace.jp/live/?cal=202612']
    doc = ConcertHTML('<a href="/yokohama/schedules">Schedule</a><a href="/tokyo/schedules?month=12&amp;year=2026">Schedule</a>')
    assert schedule_links(doc,'https://www.billboard-live.com/tokyo/schedules',NOW.date()) == ['https://www.billboard-live.com/tokyo/schedules?month=12&year=2026']
    doc = ConcertHTML('<a href="?month=2026-10-01">Schedule</a><a href="?month=2026-12-01">Schedule</a>')
    assert schedule_links(doc,'https://www.billboard-live.com/tokyo/schedules',NOW.date()) == ['https://www.billboard-live.com/tokyo/schedules?month=2026-12-01']


def test_robots_policy_is_checked_before_following_a_cross_host_redirect(monkeypatch):
    module = importlib.import_module('src.services.ArtistLiveSourceService')
    calls = []
    class Response:
        def __init__(self,status,headers=None,body=b''):
            self.status,self.headers,self.body = status,headers or {},body
        def getheader(self,name,default=None):return self.headers.get(name,default)
        def read1(self,limit):
            body,self.body = self.body,b''
            return body
    class Connection:
        sock = None
        def __init__(self,host,**kwargs):self.host = host
        def request(self,method,path,headers):
            self.path = path
            calls.append((self.host,path))
        def getresponse(self):
            if self.path == '/robots.txt':
                return Response(200,body=b'User-agent: *\nDisallow: /') if self.host=='blocked.example' else Response(404)
            return Response(302,{'Location':'https://blocked.example/show'})
        def close(self):pass
    monkeypatch.setattr(module,'_PinnedHTTPSConnection',Connection)
    with pytest.raises(module.SourceError,match='robots_disallowed'):
        module.PublicPageClient(time.monotonic()+6).html('https://public.example/show')
    assert calls == [('public.example','/robots.txt'),('public.example','/show'),('blocked.example','/robots.txt')]


def test_legacy_meta_charset_is_decoded_without_disabling_tls(monkeypatch):
    module = importlib.import_module('src.services.ArtistLiveSourceService')
    client = module.PublicPageClient(time.monotonic()+6)
    monkeypatch.setattr(client,'_check_robots',lambda _:None)
    body = '<meta charset="Shift_JIS"><main>ライブ予定</main>'.encode('shift_jis')
    monkeypatch.setattr(client,'_get',lambda *args,**kwargs:(body,'text/html',SOURCE['url']))
    assert 'ライブ予定' in client.html(SOURCE['url'])[0]


def test_legacy_same_host_http_links_are_upgraded_without_insecure_fetch():
    doc = ConcertHTML('<a href="http://cortez.jp/schedule/"><img alt="ライブ予定"></a>')
    assert schedule_links(doc,SOURCE['url']) == ['https://cortez.jp/schedule/']
    assert ConcertHTML('<a href="http://cortez.jp/show">Test Artist</a>').artist_links(WATCH.names,SOURCE['url']) == ['https://cortez.jp/show']


def test_catalog_covers_all_seven_prefectures_without_insecure_or_duplicate_urls():
    urls = [source['url'] for source in SOURCES]
    assert len(urls) == len(set(urls)) and len(urls) >= 150
    assert set(PREFECTURES) == {source['prefecture'] for source in SOURCES}
    assert all(url.startswith('https://') for url in urls)
    assert {'club','large_venue','festival','promoter'} <= {source['kind'] for source in SOURCES}


def test_tenant_on_same_host_does_not_inherit_catalogued_venue():
    assert venue_for_url('https://jazzmal20090411.wixsite.com/another-shop/schedule') is None
    assert venue_for_url('https://www.jazz.co.jp/LiveSpot/kintubo_schedule.html')['name'] == 'キンのツボ'


@pytest.mark.parametrize('case', json.loads((Path(__file__).parent/'fixtures/artist_live_sources_v2.json').read_text())['cases'], ids=lambda case: case['id'])
def test_versioned_venue_cases(case):
    events = extract_events(ConcertHTML(case['html']), case['url'], ArtistWatch('a','b',case['artist']), NOW.date())
    assert sorted({event.event_date.isoformat() for event in events}) == case['dates']


def test_embedded_calendar_is_visible_as_partially_unchecked(cache_db):
    repo, client, watches = ArtistSourceCacheRepository(), Mock(), Mock()
    client.html.return_value = ('<main><iframe src="https://www.google.com/calendar/embed"></iframe></main>', SOURCE['url'])
    watches.has_enabled.return_value = True
    assert RefreshArtistSourcesUseCase(repo,watches,lambda _:client,[SOURCE]).execute(NOW)['status'] == 'partial'
    assert '埋め込み' in repo.index()[SOURCE['url']]['reason']


@pytest.mark.parametrize('prefecture', ['茨城','栃木','群馬','Ibaraki','Tochigi','Gunma'])
def test_structured_northern_kanto_event_is_eligible(prefecture):
    event = {'@type':'MusicEvent','name':'Test Artist','startDate':'2026-12-13',
             'location':{'name':'Test Venue','address':prefecture}}
    doc = ConcertHTML('<script type="application/ld+json">'+json.dumps(event)+'</script>')
    assert len(extract_events(doc, 'https://example.com/show', WATCH, NOW.date())) == 1


def test_catalog_parser_does_not_mix_calendar_days_or_biography_with_another_show():
    html = '<main><div>2026年12月12日 OPEN 17:00 Other Artist</div><div class="biography">Test Artist live 2026年12月13日 OPEN 17:00</div></main>'
    assert extract_events(ConcertHTML(html), SOURCE['url'], WATCH, NOW.date()) == []
    mixed = '<main><div><p>2026年12月12日 OPEN 17:00 Other Artist</p><p>2026年12月13日 OPEN 17:00 Test Artist</p></div></main>'
    assert extract_events(ConcertHTML(mixed), SOURCE['url'], WATCH, NOW.date()) == []
