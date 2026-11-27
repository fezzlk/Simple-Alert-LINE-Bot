import logging
import secrets

from authlib.integrations.base_client.errors import OAuthError
from authlib.oauth2.rfc7636 import create_s256_code_challenge
from flask import flash, make_response, redirect, render_template, request, session, url_for
from google.api_core.exceptions import GoogleAPIError
from requests.exceptions import RequestException

from src.oauth_client import oauth
from src.routes.web import views_blueprint
from src.routes.web.auth import finish_line_login
from src.routes.web.helpers import build_page_contents
from src.services.LineLoginHandoff import LineLoginHandoff

handoffs = LineLoginHandoff()


def handoff_page(**values):
    page = build_page_contents(session, request, page_title="ホーム画面アプリのログイン")
    response = make_response(render_template("pages/line/handoff.html", page_contents=page, **values))
    response.headers.update({"Cache-Control": "no-store", "Pragma": "no-cache",
                             "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY"})
    return response


@views_blueprint.route("/line/handoff/start", methods=["POST"])
def start_line_handoff():
    if "login_user" in session:
        return redirect(session.pop("next_page_url", "/"))
    previous = session.pop("line_handoff", None)
    if previous:
        handoffs.revoke(previous["state"], previous["secret"])
    try:
        handoffs.cleanup()
    except GoogleAPIError:
        logging.warning("LINE login handoff cleanup unavailable")
    redirect_uri = url_for("views_blueprint.authorize", _external=True)
    state, secret, _ = handoffs.create(redirect_uri)
    session["line_handoff"] = {"state": state, "secret": secret,
                               "web_login": request.form.get("mode") == "web"}
    # A GET page survives suspension/reloading without creating a new request.
    return redirect(url_for("views_blueprint.view_line_handoff"), code=303)


@views_blueprint.route("/line/handoff", methods=["GET"])
def view_line_handoff():
    pending = session.get("line_handoff")
    saved = handoffs.for_owner(pending["state"], pending["secret"]) if pending else None
    if saved is None:
        session.pop("line_handoff", None)
        return handoff_page(error="ログインを始めたアプリから、5分以内に操作してください。")
    if saved["status"] != "pending":
        return handoff_page(stage="waiting")
    params = {"state": pending["state"], "code_challenge": create_s256_code_challenge(saved["verifier"]),
              "code_challenge_method": "S256"}
    if pending.get("web_login"):
        params["disable_auto_login"] = "true"
    try:
        authorization = oauth.create_client("line").create_authorization_url(saved["redirect_uri"], **params)
    except (OAuthError, RequestException):
        handoffs.revoke(pending["state"], pending["secret"])
        session.pop("line_handoff", None)
        return handoff_page(error="LINEに接続できませんでした。ログインをやり直してください。")
    return handoff_page(stage="waiting", authorization_url=authorization["url"],
                        web_login=pending.get("web_login", False))


def authorize_line_handoff():
    # An isolated callback never creates a Safari login session. State is
    # consumed in Firestore, then PKCE binds the code exchange to this request.
    state = request.args.get("state", "")
    saved = handoffs.begin_callback(state)
    if saved is None:
        return handoff_page(error="このログインは無効か、期限が切れています。元のアプリからやり直してください。")
    if request.args.get("error") or not request.args.get("code"):
        handoffs.fail_callback(state)
        return handoff_page(error="LINEログインがキャンセルされました。元のアプリからやり直してください。")
    try:
        line = oauth.create_client("line")
        token = line.fetch_access_token(code=request.args["code"], redirect_uri=saved["redirect_uri"],
                                        code_verifier=saved["verifier"], timeout=10)
        response = line.get("v2/profile", token=token, timeout=10)
        response.raise_for_status()
        profile = response.json()
        if not isinstance(profile, dict):
            raise ValueError("Invalid LINE profile")
        user_id, name = profile.get("userId"), profile.get("displayName")
        if not isinstance(user_id, str) or not 1 <= len(user_id) <= 128:
            raise ValueError("Missing LINE identity")
        if not isinstance(name, str) or not 1 <= len(name) <= 200:
            raise ValueError("Missing LINE display name")
        code = f"{secrets.randbelow(100_000_000):08d}"
        if not handoffs.complete_callback(state, {"userId": user_id, "displayName": name}, code):
            return handoff_page(error="ログインの期限が切れました。元のアプリからやり直してください。")
    except (OAuthError, RequestException, ValueError):
        # Do not log provider responses, codes, states or tokens.
        handoffs.fail_callback(state)
        return handoff_page(error="LINEで本人確認できませんでした。元のアプリからやり直してください。")
    pending = session.get("line_handoff") or {}
    return handoff_page(stage="code", confirmation_code=code, display_name=name,
                        can_complete_here=pending.get("state") == state)


@views_blueprint.route("/line/handoff/claim", methods=["POST"])
def claim_line_handoff():
    pending = session.get("line_handoff")
    if not pending:
        return handoff_page(error="ログインを始めたホーム画面アプリから操作してください。")
    if "login_user" in session:
        handoffs.revoke(pending["state"], pending["secret"])
        session.pop("line_handoff", None)
        return redirect(session.pop("next_page_url", "/"))
    result, profile = handoffs.consume(pending["state"], pending["secret"],
                                        request.form.get("confirmation_code", "").strip())
    if result == "ok":
        # Do not carry stale tokens, pending identities or old CSRF data across
        # the login boundary. The original, already-sanitized destination stays.
        destination = session.get("next_page_url", "/")
        session.clear()
        session["next_page_url"] = destination
        return finish_line_login(profile)
    if result in ("invalid", "expired", "locked"):
        session.pop("line_handoff", None)
        return handoff_page(error="このログインは無効か、期限が切れています。ログインをやり直してください。")
    message = "確認番号が違います。Safariに表示された8桁の番号を入力してください。"
    if result == "pending":
        message = "LINEでの本人確認が完了していません。先ほどのLINEログインを完了してください。"
    flash(message, "warning")
    return redirect(url_for("views_blueprint.view_line_handoff"), code=303)
