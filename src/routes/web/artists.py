from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from flask import abort, flash, redirect, render_template, request, session, url_for

from src import config
from src.Domains.ArtistSourceCatalog import KIND_LABELS, PREFECTURES, SOURCES
from src.Domains.Entities.ArtistWatch import normalize_name
from src.Infrastructure.Repositories import artist_source_cache_repository, artist_watch_repository
from src.Infrastructure.Repositories.ArtistWatchRepository import MONTHLY_SEARCH_LIMIT
from src.middlewares import login_required
from src.routes.web import views_blueprint
from src.routes.web.helpers import build_page_contents
from src.services.ArtistLiveSourceService import (
    build_search_queries,
    validate_source_url,
)

UTC = timezone.utc


def _owner():
    page = build_page_contents(session, request, page_title="アーティストウォッチ")
    if not page.login_user or not page.login_user._id:
        abort(401)
    return page


def _safe_checks(checks):
    safe = []
    for item in checks:
        item = dict(item)
        try:
            item["url"] = validate_source_url(str(item.get("url") or ""))
        except ValueError:
            item["url"] = ""
        if item.get("pages"):
            item["pages"] = _safe_checks(item["pages"])
        safe.append(item)
    return safe


@views_blueprint.route('/artists', methods=['GET'])
@login_required
def view_artists():
    page = _owner()
    watches = artist_watch_repository.list_for_owner(page.login_user._id)
    try:
        shared_index = artist_source_cache_repository.index(include_text=False)
    except Exception:
        shared_index = {}
    now = datetime.now(UTC)
    source_groups = []
    standard_sources = []
    for prefecture in PREFECTURES:
        group = []
        for source in SOURCES:
            if source["prefecture"] != prefecture:
                continue
            snapshot = shared_index.get(source["url"], {})
            checked_at = snapshot.get("checked_at")
            status = snapshot.get("status", "pending")
            if checked_at and (now.astimezone(ZoneInfo("Asia/Tokyo")).date() - checked_at.astimezone(ZoneInfo("Asia/Tokyo")).date()).days not in (0, 1):
                status = "stale"
            row = {**source, "title": source["name"], "status": status, "checked_at": checked_at,
                   "reason": snapshot.get("reason", ""), "page_count": snapshot.get("page_count", 0),
                   "pages": _safe_checks(snapshot.get("page_checks", []))}
            group.append(row)
            standard_sources.append(row)
        source_groups.append({"name": prefecture, "sources": group})
    source_plans = {}
    for watch in watches:
        # Keep links safe even for older or manually repaired stored snapshots.
        watch.last_page_checks = _safe_checks(watch.last_page_checks)
        sources = []
        for url in watch.source_urls:
            if url in {source["url"] for source in SOURCES}:
                continue
            try:
                url = validate_source_url(url)
            except ValueError:
                continue
            sources.append({"url": url, "title": url, "kind": "custom"})
        source_plans[watch._id] = {"sources": sources, "queries": build_search_queries(watch)}

    def local_time(value):
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                value = None
        return value.astimezone(ZoneInfo("Asia/Tokyo")).strftime("%Y/%m/%d %H:%M") if value else "まだ確認していません"

    return render_template(
        'pages/artists/index.html', page_contents=page, watches=watches, local_time=local_time,
        search_enabled=bool(config.BRAVE_SEARCH_API_KEY),
        search_used=artist_watch_repository.search_usage(datetime.now(UTC)),
        search_limit=MONTHLY_SEARCH_LIMIT,
        standard_sources=standard_sources, source_groups=source_groups, catalog_kind_labels=KIND_LABELS, source_plans=source_plans,
        source_kind_labels={"shared": "共通巡回", "standard": "標準の巡回先", "custom": "追加したURL", "linked": "公式ページから発見", "search": "Web検索から発見"},
        search_status_labels={"ok": "検索済み", "budget_exhausted": "月間上限で停止", "not_configured": "検索未設定", "error": "検索に失敗"},
    )


@views_blueprint.route('/artists/save', methods=['POST'])
@login_required
def save_artist():
    page = _owner()
    watch_id = request.form.get('watch_id', '').strip()
    name = request.form.get('artist_name', '').strip()
    aliases = list(dict.fromkeys(line.strip() for line in request.form.get('aliases', '').splitlines() if line.strip()))
    urls = list(dict.fromkeys(line.strip() for line in request.form.get('source_urls', '').splitlines() if line.strip()))
    try:
        if not name or len(name) > 100 or not normalize_name(name) or any(ord(char) < 32 for char in name):
            raise ValueError("アーティスト名は100文字以内で入力してください。")
        if len(aliases) > 10 or any(len(alias) > 100 or not normalize_name(alias) for alias in aliases):
            raise ValueError("別名は1件100文字以内、10件まで登録できます。")
        if len(urls) > 3:
            raise ValueError("追加の公式URLは3件まで登録できます。")
        urls = [validate_source_url(url) for url in urls]
        watches = artist_watch_repository.list_for_owner(page.login_user._id)
        if not watch_id and len(watches) >= 30:
            raise ValueError("アーティストは30件まで登録できます。")
        if any(watch._id != watch_id and normalize_name(watch.artist_name) == normalize_name(name) for watch in watches):
            raise ValueError("同じアーティストが登録されています。既存の登録を編集してください。")
        artist_watch_repository.save(page.login_user._id, name, aliases, urls, watch_id)
    except ValueError as error:
        flash(str(error), 'danger')
    except LookupError:
        abort(404)
    else:
        flash(f'「{name}」を保存しました。次の定期チェックから反映されます。', 'success')
    return redirect(url_for('views_blueprint.view_artists'))


@views_blueprint.route('/artists/<watch_id>/enabled', methods=['POST'])
@login_required
def toggle_artist(watch_id):
    page = _owner()
    enabled = request.form.get('enabled')
    if enabled not in ('true', 'false'):
        abort(400)
    try:
        artist_watch_repository.set_enabled(page.login_user._id, watch_id, enabled == 'true')
    except LookupError:
        abort(404)
    flash('監視を再開しました。' if enabled == 'true' else '監視を停止しました。', 'success')
    return redirect(url_for('views_blueprint.view_artists'))
