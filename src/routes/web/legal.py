from flask import render_template, session, request

from src.routes.web import views_blueprint
from src.routes.web.helpers import build_page_contents


@views_blueprint.route('/terms', methods=['GET'])
def terms():
    page_contents = build_page_contents(session, request, page_title='利用規約')
    return render_template('pages/legal/terms.html', page_contents=page_contents)


@views_blueprint.route('/privacy', methods=['GET'])
def privacy():
    page_contents = build_page_contents(session, request, page_title='プライバシーポリシー')
    return render_template('pages/legal/privacy.html', page_contents=page_contents)
