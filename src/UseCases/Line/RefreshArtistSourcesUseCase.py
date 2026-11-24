import json
import re
import time
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.parse import parse_qs, urljoin, urlsplit
from zoneinfo import ZoneInfo

from src.Domains.ArtistSourceCatalog import SOURCES
from src.services.ArtistLiveSourceService import MAX_PAGE_BYTES, ConcertHTML, PublicPageClient, _page_check

MAX_CACHED_HTML = 3 * MAX_PAGE_BYTES


def schedule_links(document, base_url, today=None):
    """At most two explicit schedule navigation links, same host and subtree."""
    parsed = urlsplit(base_url)
    today = today or datetime.now(ZoneInfo("Asia/Tokyo")).date()
    links = []
    for node in document.root.walk():
        href = node.attrs.get("href") if node.tag == "a" else None
        label = node.text() + " " + " ".join(child.attrs.get('alt', '') for child in node.walk() if child.tag == 'img') if href else ''
        if not href or not (re.search(r"schedule|スケジュール|ライブ予定|公演一覧|イベント一覧|カレンダー|live calendar", label + " " + href, re.I)
                            or re.search(r"(?:^|[/_-])live(?:[_.-]|$)", urlsplit(href).path, re.I)
                            or re.search(r"[?&]cal=20\d{4}(?:&|$)", href)
                            or re.search(r"/(?:calendar|events?|live)/?$", urlsplit(href).path, re.I)):
            continue
        url = urljoin(base_url, href).split("#", 1)[0]
        target = urlsplit(url)
        if target.scheme == "http" and target.hostname == parsed.hostname:
            target = target._replace(scheme="https")
            url = target.geturl()
        if target.scheme != "https" or target.hostname != parsed.hostname or url.rstrip('/') == base_url.rstrip('/'):
            continue
        scope = parsed.path.rstrip('/')
        leaf = scope.rsplit('/',1)[-1]
        if '.' in leaf or leaf in ('schedule','schedules','calendar','event','events'):
            scope = scope.rsplit('/',1)[0]
        if scope and not (target.path == scope or target.path.startswith(scope + '/')):
            continue
        # Do not walk archives, reservations, files, or arbitrary event details.
        if re.search(r"reserve|ticket|reservation|\.pdf|login|logout|contact", url, re.I):
            continue
        query = parse_qs(target.query)
        year = next((query[key][0] for key in ('sy', 'year') if query.get(key)), '')
        month = next((query[key][0] for key in ('sm', 'month') if query.get(key)), '')
        cal = query.get('cal',[''])[0]
        if re.fullmatch(r'20\d{4}',cal):
            year,month = cal[:4],cal[4:]
        month_date = re.fullmatch(r'(20\d{2})[-/](\d{1,2})(?:[-/]\d{1,2})?',month)
        if month_date:
            year,month = month_date.groups()
        if year.isdigit() and month.isdigit() and (int(year), int(month)) < (today.year, today.month):
            continue
        links.append(url)
    return list(dict.fromkeys(links))[:2]


class RefreshArtistSourcesUseCase:
    """One shared source per minute, once per JST day, bounded by six seconds."""
    def __init__(self, repository, watches, client_factory=PublicPageClient, sources=SOURCES):
        self.repository, self.watches = repository, watches
        self.client_factory, self.sources = client_factory, sources

    def execute(self, now=None):
        now = now or datetime.now(timezone.utc)
        if not self.watches.has_enabled():
            return {"status": "idle"}
        claimed = self.repository.claim_next(self.sources, now)
        if not claimed:
            return {"status": "idle"}
        source, token = claimed
        client = self.client_factory(time.monotonic() + 6)
        snapshot = {"title": source["name"], "status": "error", "reason": "", "page_count": 0, "failed_pages": 0, "page_checks": []}
        pages = []
        try:
            html, url = client.html(source["url"])
            document = ConcertHTML(html)
            snapshot["title"] = _page_check(url, "standard", "ok", document)["title"]
            snapshot["page_checks"].append(_page_check(url, "shared", "ok", document))
            pages.append({"url": url, "html": html})
            with ThreadPoolExecutor(max_workers=2) as pool:
                tasks = {pool.submit(client.html, link): link for link in schedule_links(document, url, now.astimezone(ZoneInfo("Asia/Tokyo")).date())}
                for future in as_completed(tasks):
                    try:
                        content, final_url = future.result()
                        pages.append({"url": final_url, "html": content})
                        snapshot["page_checks"].append(_page_check(final_url, "shared", "ok", ConcertHTML(content)))
                    except Exception as error:
                        snapshot["failed_pages"] += 1
                        snapshot["page_checks"].append(_page_check(tasks[future], "shared", "error", error=error))
            texts = []
            for page in pages:
                doc = ConcertHTML(page["html"])
                texts.append(doc.main.text())
                texts.extend(" ".join(child for child in node.children if isinstance(child, str))
                             for node in doc.root.walk() if node.tag == "script" and node.attrs.get("type") == "application/ld+json")
                if any(node.tag == 'iframe' and re.search(r'calendar|instagram', node.attrs.get('src', ''), re.I)
                       for node in doc.root.walk()):
                    snapshot['failed_pages'] += 1
                    snapshot['reason'] = '埋め込みの予定表・SNS投稿は未確認です'
            text = " ".join(texts)
            serialized = json.dumps(pages, ensure_ascii=False).encode()
            text_z = zlib.compress(text.encode())
            pages_z = zlib.compress(serialized)
            if len(serialized) > MAX_CACHED_HTML or len(text.encode()) > MAX_CACHED_HTML or len(pages_z) > 650_000 or len(text_z) > 180_000:
                snapshot["reason"] = "保存サイズの上限を超えたため、取得内容を利用できませんでした"
            else:
                snapshot.update(status="partial" if snapshot["failed_pages"] else "ok", text_z=text_z,
                                pages_z=pages_z, page_count=len(pages))
                if snapshot["failed_pages"] and not snapshot["reason"]:
                    snapshot["reason"] = "一部のスケジュールページを取得できませんでした"
        except Exception as error:
            snapshot["reason"] = _page_check(source["url"], "standard", "error", error=error)["reason"]
        self.repository.finish(source, token, snapshot, now)
        return {"status": snapshot["status"], "processed": 1}
