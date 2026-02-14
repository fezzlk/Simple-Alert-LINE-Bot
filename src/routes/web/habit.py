from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.exceptions import BadRequest

from src.Infrastructure.Repositories import habit_task_log_repository, habit_task_repository
from src.middlewares import login_required
from src.models.PageContents import HabitTaskListData, HabitTaskLogListData
from src.routes.web import views_blueprint
from src.routes.web.helpers import build_page_contents, flash_form_errors
from src.UseCases.Web.AddHabitTaskUseCase import AddHabitTaskUseCase
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


@views_blueprint.route('/habit/<task_id>', methods=['GET'])
@login_required
def view_habit_task_log(task_id: str):
    page_contents = build_page_contents(session, request, HabitTaskLogListData)
    page_contents = ViewHabitTaskLogUseCase(
        habit_task_repository=habit_task_repository,
        habit_task_log_repository=habit_task_log_repository,
    ).execute(page_contents=page_contents, task_id=task_id)
    return render_template('pages/habit/detail.html', page_contents=page_contents)
