"""Reviewed public source inventory. Listing does not imply successful extraction."""
import hashlib
import json
import zlib
from pathlib import Path
from urllib.parse import urlsplit

CATALOG = json.loads((Path(__file__).resolve().parents[1] / "data/artist_live_sources.v1.json").read_text())
SOURCES = tuple(CATALOG["sources"])
CATALOG_VERSION = hashlib.sha256(json.dumps(SOURCES, sort_keys=True).encode()).hexdigest()[:16]
PREFECTURES = ("東京", "神奈川", "千葉", "埼玉", "茨城", "栃木", "群馬", "広域")
KIND_LABELS = {"club": "ジャズ店・ライブハウス", "large_venue": "大型会場", "festival": "フェス",
               "promoter": "主催者", "association": "地域の協会"}


def unpack_cache(value: bytes, limit: int):
    decoder = zlib.decompressobj()
    output = decoder.decompress(value, limit + 1)
    if len(output) > limit or not decoder.eof or decoder.unconsumed_tail:
        raise ValueError("Invalid cache size")
    return output.decode("utf-8")


def source_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def venue_for_url(url: str):
    """Trust an explicitly catalogued venue only on its own URL subtree.

    Never infer venue from a multi-venue promoter, association or festival.
    Several venues can share hosting (Wix, blogs, rental hosting, etc.).
    """
    parsed = urlsplit(url)
    for source in sorted(SOURCES, key=lambda item: len(urlsplit(item["url"]).path), reverse=True):
        base = urlsplit(source["url"])
        if source["kind"] not in ("club", "large_venue") or source.get("fixed_venue") is False or parsed.hostname != base.hostname:
            continue
        prefix = base.path.rstrip("/")
        # Files such as /schedule.html can have sibling detail pages.
        if "." in prefix.rsplit("/", 1)[-1]:
            if sum(urlsplit(item["url"]).hostname == base.hostname for item in SOURCES) > 1 and parsed.path != base.path:
                continue
            prefix = prefix.rsplit("/", 1)[0]
        if base.query and parsed.query != base.query:
            continue
        if parsed.path == prefix or parsed.path.startswith(prefix + "/"):
            return source
    return None
