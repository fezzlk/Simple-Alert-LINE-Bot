"""Public concert discovery. Only dated, location-confirmed events become notifications.

No LLM calls, login cookies, paid scraping proxies or social-network credentials are used.
"""
import http.client
import ipaddress
import json
import re
import socket
import ssl
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date, datetime
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser
from zoneinfo import ZoneInfo

from requests.certs import where as ca_bundle

from src.Domains.Entities.ArtistWatch import ArtistWatch, ConcertEvent, matches_artist

DEFAULT_SOURCES = (
    "https://www.billboard-live.com/tokyo/schedules",
    "https://www.billboard-live.com/yokohama/schedules",
    "https://www.bluenote.co.jp/jp/artists/schedule.html",
    "https://www.cottonclubjapan.co.jp/jp/",
    "https://smash-jpn.com/",
    "https://www.creativeman.co.jp/",
)
SOURCE_NAMES = dict(zip(DEFAULT_SOURCES, (
    "Billboard Live 東京・公演スケジュール",
    "Billboard Live 横浜・公演スケジュール",
    "Blue Note Tokyo・公演スケジュール",
    "Cotton Club・公演案内",
    "SMASH・来日公演のお知らせ",
    "Creativeman・公演のお知らせ",
)))
USER_AGENT = "remily-live-watch/1.0"
MAX_PAGE_BYTES = 2 * 1024 * 1024
TOKYO = ZoneInfo("Asia/Tokyo")
METRO = re.compile(r"東京|神奈川|千葉|埼玉|横浜|川崎|さいたま|\b(?:tokyo|yokohama|kanagawa|chiba|saitama|kawasaki)\b", re.I)
DATE = re.compile(r"(?<!\d)(20\d{2})(?:\s*[年./-]\s*|\s+)(\d{1,2})\s*[月./-]\s*(\d{1,2})(?:日)?(?!\d)")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "wbr"}


class SourceError(Exception):
    pass


def validate_source_url(url: str) -> str:
    try:
        parsed = urlsplit(url.strip())
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError
        if parsed.port not in (None, 443) or len(url) > 1500:
            raise ValueError
        host = parsed.hostname.encode("idna").decode("ascii")
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
            raise ValueError
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
        if address and (not address.is_global or address.is_multicast):
            raise ValueError
        return urlunsplit(("https", parsed.netloc, parsed.path or "/", parsed.query, ""))
    except (ValueError, UnicodeError) as error:
        raise ValueError("公式URLは公開サイトのHTTPS URLを入力してください。") from error


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Connect to a validated public IP, keeping hostname verification / SNI.

    Resolving once and pinning the connection also prevents DNS rebinding between
    URL validation and the HTTP request. Every redirect is validated separately.
    """
    def connect(self):
        addresses = socket.getaddrinfo(self.host, 443, type=socket.SOCK_STREAM)
        if not addresses:
            raise SourceError("dns")
        for entry in addresses:
            address = ipaddress.ip_address(entry[4][0])
            if not address.is_global or address.is_multicast:
                raise SourceError("non_public_address")
        addresses.sort(key=lambda entry: entry[0] != socket.AF_INET)
        self.sock = socket.create_connection((addresses[0][4][0], 443), self.timeout)
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)


class PublicPageClient:
    def __init__(self, deadline: float):
        self.deadline = deadline
        self._robots = {}
        self._lock = threading.Lock()

    def _get(self, url: str, headers: dict | None = None) -> tuple[bytes, str, str]:
        original_host = urlsplit(url).hostname
        for _ in range(4):
            url = validate_source_url(url)
            remaining = self.deadline - time.monotonic()
            if remaining < 0.2:
                raise SourceError("time_limit")
            parsed = urlsplit(url)
            host = parsed.hostname.encode("idna").decode("ascii")
            if headers and host != original_host:
                raise SourceError("cross_host_redirect")
            connection = _PinnedHTTPSConnection(
                host, timeout=min(2.5, remaining), context=ssl.create_default_context(cafile=ca_bundle())
            )
            try:
                connection.request("GET", urlunsplit(("", "", parsed.path or "/", parsed.query, "")),
                                   headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity", **(headers or {})})
                response = connection.getresponse()
                if response.status in (301, 302, 303, 307, 308):
                    location = response.getheader("Location")
                    if not location:
                        raise SourceError("redirect")
                    url = urljoin(url, location)
                    continue
                if response.status != 200:
                    raise SourceError(f"http_{response.status}")
                if response.getheader("Content-Encoding", "identity") != "identity":
                    raise SourceError("unsupported_encoding")
                chunks = []
                total = 0
                while total <= MAX_PAGE_BYTES:
                    remaining = self.deadline - time.monotonic()
                    if remaining <= 0:
                        raise SourceError("time_limit")
                    if connection.sock:
                        connection.sock.settimeout(min(2.5, remaining))
                    chunk = response.read1(min(65536, MAX_PAGE_BYTES + 1 - total))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    total += len(chunk)
                body = b"".join(chunks)
                if len(body) > MAX_PAGE_BYTES:
                    raise SourceError("page_too_large")
                return body, response.getheader("Content-Type", ""), url
            finally:
                connection.close()
        raise SourceError("too_many_redirects")

    def html(self, url: str) -> tuple[str, str]:
        url = validate_source_url(url)
        parsed = urlsplit(url)
        origin = f"https://{parsed.netloc}"
        # Cache per source scan; no credentials or browser state are retained.
        with self._lock:
            policy = self._robots.get(origin)
        if policy is None:
            policy = RobotFileParser()
            try:
                body, _, _ = self._get(origin + "/robots.txt")
                policy.parse(body.decode("utf-8", errors="replace").splitlines())
            except SourceError as error:
                if str(error) not in ("http_404", "http_410"):
                    raise
                policy.parse([])
            with self._lock:
                self._robots[origin] = policy
        if not policy.can_fetch(USER_AGENT, url):
            raise SourceError("robots_disallowed")
        body, content_type, final_url = self._get(url)
        if "html" not in content_type.lower():
            raise SourceError("not_html")
        charset = re.search(r"charset=[\"']?([\w-]+)", content_type, re.I)
        encoding = charset.group(1) if charset else "utf-8"
        try:
            return body.decode(encoding, errors="replace"), final_url
        except LookupError as error:
            raise SourceError("encoding") from error

    def search(self, query: str, api_key: str) -> list[str]:
        url = "https://api.search.brave.com/res/v1/web/search?" + urlencode(
            {"q": query, "count": 8, "country": "JP", "safesearch": "moderate"}
        )
        body, _, _ = self._get(url, {"X-Subscription-Token": api_key, "Accept": "application/json"})
        result = json.loads(body)
        return [item["url"] for section in ("web", "news")
                for item in result.get(section, {}).get("results", []) if isinstance(item.get("url"), str)]


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    parent: "Node | None" = field(default=None, repr=False)

    def text(self) -> str:
        if self.tag in ("script", "style", "nav", "footer", "header"):
            return ""
        return re.sub(r"\s+", " ", " ".join(child.text() if isinstance(child, Node) else child for child in self.children)).strip()

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()


class ConcertHTML(HTMLParser):
    def __init__(self, html: str):
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), parent=self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    @property
    def main(self):
        return next((node for node in self.root.walk() if node.tag == "main"), self.root)

    def artist_links(self, names: list[str], base_url: str) -> list[str]:
        links = []
        for node in self.main.walk():
            if node.tag != "a" or not node.attrs.get("href"):
                continue
            text = node.text()
            if node.parent and len(node.parent.text()) <= 600 and sum(child.tag == "a" for child in node.parent.walk()) <= 2:
                text += " " + node.parent.text()
            if matches_artist(text, names):
                try:
                    links.append(validate_source_url(urljoin(base_url, node.attrs["href"])))
                except ValueError:
                    continue
        return list(dict.fromkeys(links))


def _objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _objects(child)


def _event_status(text: str) -> str:
    if re.search(r"EventCancelled|公演中止|開催中止|公演キャンセル|\bcancel(?:led|ed)\b", text, re.I):
        return "cancelled"
    if re.search(r"EventPostponed|公演延期|開催延期|\bpostponed\b", text, re.I):
        return "postponed"
    return "scheduled"


def _date_values(text: str) -> list[date]:
    values = []
    for match in DATE.finditer(text):
        try:
            values.append(date(*map(int, match.groups())))
        except ValueError:
            continue
    return list(dict.fromkeys(values))


def _schedule_dates(text: str) -> list[date]:
    """Expand the venue's explicit date list: '2027 3.21 sun., 3.22 mon.'.

    Used only on the actual show's date element, never on biography / sidebar text.
    """
    year = None
    previous_month = None
    values = []
    for match in re.finditer(r"(?:(20\d{2})\s*[年./-]?\s*)?(\d{1,2})[月./-](\d{1,2})(?!\d)", text):
        explicit_year, month, day = match.groups()
        month, day = int(month), int(day)
        if explicit_year:
            year = int(explicit_year)
        elif year and previous_month and previous_month - month > 6:
            year += 1
        if not year:
            continue
        try:
            values.append(date(year, month, day))
            previous_month = month
        except ValueError:
            continue
    return list(dict.fromkeys(values))


def _structured_events(document: ConcertHTML, url: str, watch: ArtistWatch, today: date) -> list[ConcertEvent]:
    events = []
    for script in document.root.walk():
        if script.tag != "script" or script.attrs.get("type") != "application/ld+json":
            continue
        try:
            data = json.loads("".join(child for child in script.children if isinstance(child, str)))
        except (ValueError, TypeError):
            continue
        for item in _objects(data):
            kind = item.get("@type", [])
            kind = [kind] if isinstance(kind, str) else kind
            if not any(value in ("MusicEvent", "Event", "Festival") for value in kind):
                continue
            performers = json.dumps(item.get("performer", []), ensure_ascii=False)
            title = str(item.get("name", ""))
            # Do not match an artist mentioned only in background / influence / related shows.
            if not matches_artist(title + " " + performers, watch.names):
                continue
            location = item.get("location", {})
            if not isinstance(location, dict):
                continue
            location_text = json.dumps(location, ensure_ascii=False)
            if not METRO.search(location_text):
                continue
            venue = str(location.get("name", "")).strip()
            if not venue:
                continue
            try:
                start = str(item["startDate"])
                when = (datetime.fromisoformat(start.replace("Z", "+00:00")).astimezone(TOKYO).date()
                        if "T" in start and ("+" in start[10:] or start.endswith("Z")) else date.fromisoformat(start[:10]))
            except (ValueError, KeyError, TypeError):
                continue
            if when < today:
                continue
            offers = item.get("offers", [])
            offers = [offers] if isinstance(offers, dict) else offers
            ticket_info = " / ".join(sorted({str(offer["validFrom"]) for offer in offers
                                              if isinstance(offer, dict) and offer.get("validFrom")}))
            events.append(ConcertEvent(title[:200], when, venue[:120], url,
                                       _event_status(str(item.get("eventStatus", ""))), ticket_info[:500]))
    return events


def extract_events(document: ConcertHTML, url: str, watch: ArtistWatch, today: date) -> list[ConcertEvent]:
    structured = _structured_events(document, url, watch, today)
    if structured:
        return structured
    parsed = urlsplit(url)
    headings = [node.text() for node in document.main.walk() if node.tag == "h1"]
    title = next((heading for heading in headings if matches_artist(heading, watch.names)), "")
    text = document.main.text()
    # Venue adapters separate the actual show from recommendations and other tour stops.
    venue = ""
    ticket_info = ""
    if parsed.hostname in ("www.billboard-live.com", "billboard-live.com"):
        if parsed.path == "/tokyo/show":
            venue = "Billboard Live TOKYO"
        elif parsed.path == "/yokohama/show":
            venue = "Billboard Live YOKOHAMA"
        else:
            return []
        text = re.split(r"\bNotice\b|\bTour Information\b|\bRecommended\b", text, maxsplit=1)[0]
        members = re.search(r"\bMember\b(.*?)(?:Open\s*/\s*Start|$)", text, re.I)
        if not matches_artist(title, watch.names) and not (members and matches_artist(members.group(1), watch.names)):
            return []
        if not title:
            title = next((heading for heading in headings if heading.casefold() not in ("tokyo", "yokohama", "osaka")), watch.artist_name)
        date_header = re.split(r"\bOverview\b|\bMember\b", text, maxsplit=1)[0]
        dates = _schedule_dates(date_header)
    elif parsed.hostname == "www.bluenote.co.jp" and re.match(r"/jp/artists/[^/]+/?$", parsed.path):
        if parsed.path.endswith("schedule.html"):
            return []
        venue = "BLUE NOTE TOKYO"
        nodes = list(document.main.walk())
        title = next((node.text() for node in nodes if node.tag in ("h1", "h2")), "")
        # The member table is distinct from the biography, past shows and recommendations.
        members = [node.text() for node in nodes if node.tag == "table" and len(node.text()) < 5000]
        if not matches_artist(title + " " + " ".join(members), watch.names):
            return []
        date_text = next((node.text() for node in nodes if "date" in node.attrs.get("class", "").split()), "")
        dates = _schedule_dates(date_text)
        ticket_info = next((node.text() for node in nodes if node.attrs.get("id") == "ticketPanelTop"), "")[:500]
        text = title + " " + " ".join(members)
    elif parsed.hostname in ("www.cottonclubjapan.co.jp", "cottonclubjapan.co.jp") and re.match(r"/jp/(?:sp/)?artists/[^/]+/?$", parsed.path):
        venue = "COTTON CLUB Tokyo"
        members = re.search(r"\bMEMBER\b(.*?)(?:[＜<]予約受付開始日|\bCHARGE\b|$)", text, re.I)
        if not matches_artist(title, watch.names) and not (members and matches_artist(members.group(1), watch.names)):
            return []
        dates_text = next((node.text() for node in document.main.walk()
                           if "artist_date" in node.attrs.get("class", "").split()), "")
        dates = _schedule_dates(dates_text)
        reservation = re.search(r"[＜<]予約受付開始日[＞>](.*?)(?:※この公演|ご予約はこちら|CHARGE|$)", text)
        ticket_info = reservation.group(1).strip()[:500] if reservation else ""
        text = title + " " + (members.group(1) if members else "")
    else:
        # General promoters / ticket pages: inspect individual event blocks, never the
        # page footer or an unrelated Tokyo date elsewhere in a nationwide tour.
        events = []
        block_tags = ("article", "section", "li", "p", "tr", "div")
        for node in document.main.walk():
            if node.tag not in block_tags:
                continue
            block = node.text()
            if len(block) > 1800 or not matches_artist(title + " " + block, watch.names):
                continue
            region = METRO.search(block)
            if not region:
                continue
            if any(child is not node and child.tag in block_tags and _date_values(child.text())
                   and re.search(r"会場|\bVenue\b", child.text(), re.I) for child in node.walk()):
                # Read individual tour stops instead of pairing every date with
                # the first venue in a parent article containing several cities.
                continue
            # Match a date and location in the same small block.
            for when in _date_values(block):
                if when >= today:
                    venue_match = re.search(r"(?:会場|Venue)\s*[:：]?\s*(.{2,100}?)(?=\s(?:開場|開演|OPEN|START|料金|チケット)|$)", block, re.I)
                    if not venue_match:
                        continue
                    events.append(ConcertEvent(title or watch.artist_name, when, venue_match.group(1).strip(),
                                               url, _event_status(block)))
        return events
    if not matches_artist(title + " " + text, watch.names):
        return []
    return [ConcertEvent(title or watch.artist_name, when, venue, url, _event_status(text), ticket_info)
            for when in dates if when >= today]


@dataclass
class DiscoveryResult:
    events: list[ConcertEvent] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_pages: int = 0
    page_checks: list[dict] = field(default_factory=list)
    search_checks: list[dict] = field(default_factory=list)
    skipped_details: int = 0


def build_search_queries(watch: ArtistWatch) -> list[str]:
    jp_name = next((name for name in watch.names if re.search(r"[^\x00-\x7f]", name)), watch.artist_name)
    en_name = next((name for name in watch.names if name.isascii()), watch.artist_name)
    return [f'"{jp_name}" (来日 OR 公演 OR ライブ) (東京 OR 横浜 OR 千葉 OR 埼玉)',
            f'"{en_name}" (Tokyo OR Yokohama OR Chiba OR Saitama) (live OR tour OR tickets)']


def _page_check(url: str, kind: str, status: str, document=None, error=None) -> dict:
    # Only our HTTP observations and independently fetched page titles are saved;
    # no Brave result titles, snippets, response bodies or unfetched result URLs.
    try:
        url = validate_source_url(url)
    except ValueError:
        url = ""
    title = ""
    if document:
        title = next((node.text() for node in document.root.walk() if node.tag == "title"), "")
        title = title or next((node.text() for node in document.main.walk() if node.tag == "h1"), "")
    reason = ""
    if error:
        code = str(error) if isinstance(error, SourceError) else "fetch_failed"
        if re.fullmatch(r"http_\d{3}", code):
            reason = f"HTTP {code[5:]}"
        else:
            reason = {
                "robots_disallowed": "サイトの自動取得ルールにより対象外",
                "time_limit": "確認時間の上限に到達",
                "non_public_address": "公開サイト以外のため対象外",
                "not_html": "対応していないページ形式",
                "page_too_large": "ページのサイズ上限を超過",
            }.get(code, "ページを取得できませんでした")
    return {"url": url, "title": (title or SOURCE_NAMES.get(url) or urlsplit(url).hostname or "取得対象外のURL")[:200],
            "kind": kind, "status": status, "reason": reason, "event_count": 0, "candidate_links": 0}


class ArtistLiveSourceService:
    def __init__(self, api_key: str = "", client_factory=PublicPageClient):
        self.api_key = api_key
        self.client_factory = client_factory

    def discover(self, watch: ArtistWatch, today: date, reserve_search, deadline: float) -> DiscoveryResult:
        client = self.client_factory(deadline)
        result = DiscoveryResult()
        pages = []
        search_urls = []

        def page(url):
            html, final_url = client.html(url)
            return final_url, ConcertHTML(html)

        def search(query):
            if not reserve_search():
                return [], "検索の月間無料枠向け上限に達しました。公式サイト巡回は継続します。"
            return client.search(query, self.api_key), ""

        queries = build_search_queries(watch)
        sources = list(dict.fromkeys([*watch.source_urls, *DEFAULT_SOURCES]))
        with ThreadPoolExecutor(max_workers=4) as pool:
            tasks = {pool.submit(page, url): ("page", url) for url in sources}
            if self.api_key:
                tasks.update({pool.submit(search, query): ("search", query) for query in queries})
            else:
                result.warnings.append("横断検索は未設定です。公式サイト巡回のみ実行しました。")
                result.search_checks = [{"query": query, "status": "not_configured"} for query in queries]
            for task in as_completed(tasks):
                kind, source = tasks[task]
                try:
                    value, detail = task.result()
                    if kind == "page":
                        record = _page_check(value, "standard" if source in DEFAULT_SOURCES else "custom", "ok", detail)
                        result.page_checks.append(record)
                        pages.append((value, detail, record))
                        result.checked_pages += 1
                    else:
                        search_urls.extend(value)
                        result.search_checks.append({"query": source, "status": "budget_exhausted" if detail else "ok"})
                        if detail:
                            result.warnings.append(detail)
                except Exception as error:
                    # Do not include upstream exceptions: they may contain request headers / API keys.
                    if kind == "page":
                        result.page_checks.append(_page_check(
                            source, "standard" if source in DEFAULT_SOURCES else "custom", "error", error=error
                        ))
                    else:
                        result.search_checks.append({"query": source, "status": "error"})
                    label = urlsplit(source).hostname if kind == "page" else "Web横断検索"
                    result.warnings.append(f"{label} を取得できませんでした。")

            candidates = []
            candidate_kinds = {}

            def inspect_page(url, document, record, collect_links=True):
                try:
                    events = extract_events(document, url, watch, today)
                    result.events.extend(events)
                    record["event_count"] = len({event.key(watch.artist_name) for event in events})
                    return document.artist_links(watch.names, url) if collect_links else []
                except Exception:
                    record.update(status="parse_error", reason="ページは取得できましたが公演情報を読み取れませんでした")
                    result.warnings.append(f"{urlsplit(url).hostname} の公演情報を読み取れませんでした。")
                    return []

            for url, document, record in pages:
                links = inspect_page(url, document, record)
                record["candidate_links"] = len(links)
                candidates.extend(links)
                candidate_kinds.update({link: "linked" for link in links})
            candidates.extend(search_urls)
            for url in search_urls:
                candidate_kinds.setdefault(url, "search")
            visited = {url for url, _, _ in pages}
            candidates = [url for url in dict.fromkeys(candidates) if url not in visited]
            result.skipped_details = max(0, len(candidates) - 8)
            candidates = candidates[:8]
            if candidates and time.monotonic() >= deadline - 1:
                result.warnings.append("確認時間の上限に達し、一部の詳細ページを確認できませんでした。")
                result.skipped_details += len(candidates)
                candidates = []
            details = {pool.submit(page, url): url for url in candidates}
            for task in as_completed(details):
                try:
                    url, document = task.result()
                    result.checked_pages += 1
                    record = _page_check(url, candidate_kinds[details[task]], "ok", document)
                    result.page_checks.append(record)
                    inspect_page(url, document, record, collect_links=False)
                except Exception as error:
                    record = _page_check(details[task], candidate_kinds[details[task]], "error", error=error)
                    result.page_checks.append(record)
                    label = urlsplit(record["url"]).hostname or "一部のページ"
                    result.warnings.append(f"{label} の詳細を取得できませんでした。")
        # Group the same artist/date/venue even if announced on several sites.
        unique = {}
        for event in result.events:
            key = event.key(watch.artist_name)
            existing = unique.get(key)
            if existing is None or event.status != "scheduled" or (event.ticket_info and not existing.ticket_info):
                unique[key] = event
        result.events = sorted(unique.values(), key=lambda event: (event.event_date, event.venue))
        result.warnings = list(dict.fromkeys(result.warnings))
        kind_order = {"standard": 0, "custom": 1, "linked": 2, "search": 3}
        result.page_checks.sort(key=lambda item: (kind_order[item["kind"]], item["title"], item["url"]))
        result.search_checks.sort(key=lambda item: queries.index(item["query"]))
        return result
