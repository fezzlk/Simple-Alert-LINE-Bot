from flask import flash
from flask.sessions import SessionMixin
from flask import Request

from src.models.PageContents import PageContents
from src.web_context import build_login_user


def flash_form_errors(form) -> None:
    for field, errors in form.errors.items():
        for err in errors:
            flash(f'{field}: {err}', 'danger')


def build_page_contents(
    session: SessionMixin,
    request: Request,
    DataClass=None,
    page_title: str = '',
) -> PageContents:
    page_contents = PageContents(session, request, DataClass, page_title)
    page_contents.login_user = build_login_user(session)
    return page_contents


def capture_next_url(session: SessionMixin, request: Request) -> None:
    next_url = request.args.get('next')
    if next_url:
        session['next_page_url'] = next_url
