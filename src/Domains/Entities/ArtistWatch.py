import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime


def normalize_name(value: str) -> str:
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", value).casefold())


def matches_artist(text: str, names: list[str]) -> bool:
    text = unicodedata.normalize("NFKC", text).casefold()
    for name in names:
        name = unicodedata.normalize("NFKC", name).strip().casefold()
        if not name:
            continue
        # Latin names need boundaries: 'Chris Dave' must not match 'Chris Davenport'.
        if re.fullmatch(r"[\x00-\x7f]+", name):
            pattern = r"(?<![a-z0-9])" + r"[\s\W_]*".join(map(re.escape, name.split())) + r"(?![a-z0-9])"
            if re.search(pattern, text):
                return True
        elif normalize_name(name) in normalize_name(text):
            return True
    return False


@dataclass
class ArtistWatch:
    _id: str
    owner_id: str
    artist_name: str
    aliases: list[str] = field(default_factory=list)
    source_urls: list[str] = field(default_factory=list)
    enabled: bool = True
    next_check_at: datetime | None = None
    last_checked_at: datetime | None = None
    last_scan_day: str = ""
    status: str = "waiting"
    warnings: list[str] = field(default_factory=list)
    last_page_checks: list[dict] = field(default_factory=list)
    last_search_checks: list[dict] = field(default_factory=list)
    last_skipped_details: int = 0

    @property
    def names(self) -> list[str]:
        return [self.artist_name, *self.aliases]

    @classmethod
    def from_document(cls, document_id: str, data: dict):
        fields = cls.__dataclass_fields__
        return cls(**{**{k: v for k, v in data.items() if k in fields}, "_id": document_id})


@dataclass(frozen=True)
class ConcertEvent:
    title: str
    event_date: date
    venue: str
    source_url: str
    status: str = "scheduled"
    ticket_info: str = ""

    def key(self, artist_name: str) -> str:
        identity = [normalize_name(artist_name), self.event_date.isoformat(), normalize_venue(self.venue)]
        return hashlib.sha256("|".join(identity).encode()).hexdigest()

    @property
    def fingerprint(self) -> str:
        # Headlines, tracking URLs and page decoration are not new concert information.
        material = [self.status, re.sub(r"\s+", " ", self.ticket_info).strip()]
        return hashlib.sha256(json.dumps(material, ensure_ascii=False).encode()).hexdigest()

    def to_dict(self) -> dict:
        return {**self.__dict__, "event_date": self.event_date.isoformat()}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**{**data, "event_date": date.fromisoformat(data["event_date"])})


def normalize_venue(value: str) -> str:
    normalized = normalize_name(value)
    for canonical, names in {
        "billboardlivetokyo": ("billboardlivetokyo", "ビルボードライブ東京"),
        "billboardliveyokohama": ("billboardliveyokohama", "ビルボードライブ横浜"),
        "bluenotetokyo": ("bluenotetokyo", "ブルーノート東京"),
        "cottonclubtokyo": ("cottonclub", "コットンクラブ"),
    }.items():
        if any(name in normalized for name in names):
            return canonical
    return normalized
