from flask import render_template, session, request

from src.routes.web import views_blueprint
from src.routes.web.helpers import build_page_contents
from src import config


@views_blueprint.route('/', methods=['GET'])
def index():
    page_contents = build_page_contents(session, request)
    return render_template(
        'pages/index.html',
        page_contents=page_contents,
        line_add_friends_url=config.LINE_ADD_FRIENDS_URL,
    )
