from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.exceptions import BadRequest

from src.Infrastructure.Repositories import habit_task_log_repository, habit_task_repository
from src.middlewares import login_required
from src.models.PageContents import HabitTaskListData, HabitTaskLogListData
from src.routes.web import views_blueprint
from src.routes.web.helpers import build_page_contents, flash_form_errors
from src.UseCases.Web.AddHabitTaskUseCase import AddHabitTaskUseCase
from src.UseCases.Web.UpdateHabitTaskUseCase import UpdateHabitTaskUseCase
from src.UseCases.Web.DeleteHabitTaskUseCase import DeleteHabitTaskUseCase
from src.UseCases.Web.UpdateHabitTaskLogUseCase import UpdateHabitTaskLogUseCase
from src.UseCases.Web.ViewHabitTaskListUseCase import ViewHabitTaskListUseCase
from src.UseCases.Web.ViewHabitTaskLogUseCase import ViewHabitTaskLogUseCase
from src.models.Forms.AddHabitTaskForm import AddHabitTaskForm


@views_blueprint.route('/habit', methods=['GET'])
@login_required
def view_habit_task_list():
    page_contents = build_page_contents(session, request, HabitTaskListData)
    page_contents, form = ViewHabitTaskListUseCase(
        habit_task_repository=habit_task_repository
    ).execute(page_contents=page_contents)
    return render_template('pages/habit/index.html', page_contents=page_contents, form=form)


@views_blueprint.route('/habit', methods=['POST'])
@login_required
def add_habit_task():
    page_contents = build_page_contents(session, request)
    try:
        task_name = AddHabitTaskUseCase(
            habit_task_repository=habit_task_repository
        ).execute(page_contents=page_contents)
    except BadRequest:
        form = AddHabitTaskForm(request.form)
        flash_form_errors(form)
        page_contents = build_page_contents(session, request, HabitTaskListData)
        page_contents, _ = ViewHabitTaskListUseCase(
            habit_task_repository=habit_task_repository
        ).execute(page_contents=page_contents)
        return render_template('pages/habit/index.html', page_contents=page_contents, form=form)
    flash(f'習慣タスク「{task_name}」を追加しました。', 'success')
    return redirect(url_for('views_blueprint.view_habit_task_list'))


@views_blueprint.route('/habit/update', methods=['POST'])
@login_required
def update_habit_task():
    page_contents = build_page_contents(session, request)
    try:
        task_name = UpdateHabitTaskUseCase(
            habit_task_repository=habit_task_repository
        ).execute(page_contents=page_contents)
    except BadRequest as e:
        flash(str(e), 'danger')
        return redirect(url_for('views_blueprint.view_habit_task_list'))
    flash(f'習慣タスク「{task_name}」を更新しました。', 'success')
    return redirect(url_for('views_blueprint.view_habit_task_list'))


@views_blueprint.route('/habit/delete', methods=['POST'])
@login_required
def delete_habit_task():
    page_contents = build_page_contents(session, request)
    try:
        task_name = DeleteHabitTaskUseCase(
            habit_task_repository=habit_task_repository
        ).execute(page_contents=page_contents)
    except BadRequest as e:
        flash(str(e), 'danger')
        return redirect(url_for('views_blueprint.view_habit_task_list'))
    flash(f'習慣タスク「{task_name}」を停止しました。', 'success')
    return redirect(url_for('views_blueprint.view_habit_task_list'))


@views_blueprint.route('/habit/reactivate', methods=['POST'])
@login_required
def reactivate_habit_task():
    page_contents = build_page_contents(session, request)
    form = page_contents.request.form
    task_id = form.get("task_id", "").strip()
    if not task_id:
        flash("タスクIDが指定されていません。", "danger")
        return redirect(url_for('views_blueprint.view_habit_task_list'))

    login_user = page_contents.login_user
    owner_ids = [login_user._id]
    if login_user.linked_line_user_id:
        owner_ids.append(login_user.linked_line_user_id)

    tasks = habit_task_repository.find({"_id": task_id, "is_active": False})
    if not tasks or tasks[0].owner_id not in owner_ids:
        flash("タスクが見つかりません。", "danger")
        return redirect(url_for('views_blueprint.view_habit_task_list'))

    habit_task_repository.update(
        query={"_id": task_id},
        new_values={"is_active": True},
    )
    flash(f'習慣タスク「{tasks[0].task_name}」を再開しました。', 'success')
    return redirect(url_for('views_blueprint.view_habit_task_list'))


@views_blueprint.route('/habit/<task_id>', methods=['GET'])
@login_required
def view_habit_task_log(task_id: str):
    page_contents = build_page_contents(session, request, HabitTaskLogListData)
    month = request.args.get("month")
    page_contents = ViewHabitTaskLogUseCase(
        habit_task_repository=habit_task_repository,
        habit_task_log_repository=habit_task_log_repository,
    ).execute(page_contents=page_contents, task_id=task_id, month=month)
    return render_template('pages/habit/detail.html', page_contents=page_contents)


@views_blueprint.route('/habit/<task_id>/log', methods=['POST'])
@login_required
def update_habit_task_log(task_id: str):
    page_contents = build_page_contents(session, request)
    month = request.form.get("month", "")
    try:
        UpdateHabitTaskLogUseCase(
            habit_task_repository=habit_task_repository,
            habit_task_log_repository=habit_task_log_repository,
        ).execute(page_contents=page_contents)
    except BadRequest as e:
        flash(str(e), 'danger')
        return redirect(url_for('views_blueprint.view_habit_task_log', task_id=task_id, month=month))
    flash('実績を更新しました。', 'success')
    return redirect(url_for('views_blueprint.view_habit_task_log', task_id=task_id, month=month))
