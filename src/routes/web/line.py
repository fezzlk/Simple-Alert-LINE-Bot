from flask import render_template, url_for, redirect, session, request

from src.routes.web import views_blueprint
from src.middlewares import login_required
from src.routes.web.helpers import build_page_contents
from src.UseCases.Web.ViewApproveLinkLineUseCase import ViewApproveLinkLineUseCase
from src.UseCases.Web.ApproveLinkLineUserUseCase import ApproveLinkLineUserUseCase
from src.UseCases.Web.RegisterLineUserUseCase import RegisterLineUserUseCase
from src.models.Forms.LineRegisterForm import LineRegisterForm
from src.routes.web.helpers import flash_form_errors
from src.Infrastructure.Repositories import line_user_repository, web_user_repository


@views_blueprint.route('/line/approve', methods=['GET'])
@login_required
def view_approve_link_line_user():
    page_contents = build_page_contents(session, request)
    page_contents = ViewApproveLinkLineUseCase(
        line_user_repository=line_user_repository,
    ).execute(page_contents=page_contents)
    return render_template('pages/line/approve.html', page_contents=page_contents)


@views_blueprint.route('/line/approve', methods=['POST'])
@login_required
def approve_line_user():
    page_contents = build_page_contents(session, request)
    ApproveLinkLineUserUseCase(
        web_user_repository=web_user_repository,
    ).execute(page_contents=page_contents)
    return redirect(url_for('views_blueprint.view_approve_link_line_user'))


@views_blueprint.route('/line/register', methods=['GET'])
def line_register():
    pending = session.get('pending_line_user')
    if not pending:
        return redirect(url_for('views_blueprint.login'))

    form = LineRegisterForm()
    form.web_user_name.data = pending.get('display_name') or ''
    page_contents = build_page_contents(session, request)
    return render_template('pages/line/register.html', form=form, page_contents=page_contents)


@views_blueprint.route('/line/register', methods=['POST'])
def line_register_post():
    pending = session.get('pending_line_user')
    if not pending:
        return redirect(url_for('views_blueprint.login'))

    form = LineRegisterForm(request.form)
    if not form.validate():
        flash_form_errors(form)
        page_contents = build_page_contents(session, request)
        return render_template('pages/line/register.html', form=form, page_contents=page_contents)

    new_web_user = RegisterLineUserUseCase(
        web_user_repository=web_user_repository,
    ).execute(
        line_user_id=pending.get('line_user_id'),
        web_user_name=form.web_user_name.data,
    )
    session.pop('pending_line_user', None)
    session['login_user'] = {
        '_id': str(new_web_user._id),
        'web_user_name': new_web_user.web_user_name,
        'web_user_email': new_web_user.web_user_email,
        'linked_line_user_id': new_web_user.linked_line_user_id,
        'is_linked_line_user': new_web_user.is_linked_line_user,
    }

    redirect_to = session.pop('next_page_url', '/')
    return redirect(redirect_to)
