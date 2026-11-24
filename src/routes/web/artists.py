from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from flask import abort, flash, redirect, render_template, request, session, url_for

from src import config
from src.Domains.Entities.ArtistWatch import normalize_name
from src.Infrastructure.Repositories import artist_watch_repository
from src.Infrastructure.Repositories.ArtistWatchRepository import MONTHLY_SEARCH_LIMIT
from src.middlewares import login_required
from src.routes.web import views_blueprint
from src.routes.web.helpers import build_page_contents
from src.services.ArtistLiveSourceService import validate_source_url

UTC = timezone.utc


def _owner():
    page = build_page_contents(session, request, page_title="アーティストウォッチ")
    if not page.login_user or not page.login_user._id:
        abort(401)
    return page


@views_blueprint.route('/artists', methods=['GET'])
@login_required
def view_artists():
    page = _owner()
    watches = artist_watch_repository.list_for_owner(page.login_user._id)

    def local_time(value):
        return value.astimezone(ZoneInfo("Asia/Tokyo")).strftime("%Y/%m/%d %H:%M") if value else "まだ確認していません"

    return render_template(
        'pages/artists/index.html', page_contents=page, watches=watches, local_time=local_time,
        search_enabled=bool(config.BRAVE_SEARCH_API_KEY),
        search_used=artist_watch_repository.search_usage(datetime.now(UTC)),
        search_limit=MONTHLY_SEARCH_LIMIT,
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
