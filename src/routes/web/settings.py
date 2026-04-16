import logging

from flask import flash, redirect, render_template, request, session, url_for

from src.Infrastructure.Repositories import web_user_repository
from src.middlewares import login_required
from src.routes.web import views_blueprint
from src.routes.web.helpers import build_page_contents
from src.services.encryption import decrypt_api_key, encrypt_api_key

logger = logging.getLogger(__name__)


def _mask_api_key(plaintext: str) -> str:
    """Mask an API key, showing only 'sk-...****' + last 4 chars."""
    if len(plaintext) <= 7:
        return "sk-...****"
    return f"sk-...****{plaintext[-4:]}"


@views_blueprint.route('/settings', methods=['GET'])
@login_required
def view_settings():
    page_contents = build_page_contents(session, request, page_title='設定')
    login_user = page_contents.login_user

    masked_key = None
    if login_user and login_user._id:
        users = web_user_repository.find({"_id": login_user._id})
        if users:
            user = users[0]
            encrypted_key = getattr(user, 'openai_api_key', None)
            if encrypted_key:
                plaintext = decrypt_api_key(encrypted_key)
                if plaintext:
                    masked_key = _mask_api_key(plaintext)

    return render_template(
        'pages/settings.html',
        page_contents=page_contents,
        masked_key=masked_key,
    )


@views_blueprint.route('/settings', methods=['POST'])
@login_required
def save_settings():
    page_contents = build_page_contents(session, request, page_title='設定')
    login_user = page_contents.login_user

    if not login_user or not login_user._id:
        flash('ユーザー情報が見つかりません。', 'danger')
        return redirect(url_for('views_blueprint.view_settings'))

    api_key = request.form.get('openai_api_key', '').strip()

    # Clear the key if empty value submitted
    if not api_key:
        web_user_repository.update(
            query={"_id": login_user._id},
            new_values={"openai_api_key": None},
        )
        flash('OpenAI APIキーをクリアしました。', 'success')
        return redirect(url_for('views_blueprint.view_settings'))

    # Validate key format
    if not api_key.startswith('sk-') or len(api_key) <= 20:
        flash('APIキーの形式が正しくありません。「sk-」で始まる21文字以上のキーを入力してください。', 'danger')
        return redirect(url_for('views_blueprint.view_settings'))

    # Encrypt and save
    try:
        encrypted_key = encrypt_api_key(api_key)
    except Exception as e:
        logger.error("Failed to encrypt API key: %s", e)
        flash('APIキーの暗号化に失敗しました。管理者に連絡してください。', 'danger')
        return redirect(url_for('views_blueprint.view_settings'))

    web_user_repository.update(
        query={"_id": login_user._id},
        new_values={"openai_api_key": encrypted_key},
    )
    flash('OpenAI APIキーを保存しました。', 'success')
    return redirect(url_for('views_blueprint.view_settings'))
