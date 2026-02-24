from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from flask import render_template, request, session

from src.routes.web import views_blueprint
from src.routes.web.helpers import build_page_contents
from src import config
from src.Infrastructure.Repositories import (
    habit_task_log_repository,
    habit_task_repository,
    notification_schedule_repository,
    stock_repository,
)


def _build_owner_ids(page_contents) -> list[str]:
    login_user = page_contents.login_user
    if login_user is None:
        return []
    owner_ids = [login_user._id]
    if login_user.linked_line_user_id:
        owner_ids.insert(0, login_user.linked_line_user_id)
    return [owner_id for owner_id in owner_ids if owner_id]


@views_blueprint.route('/', methods=['GET'])
def index():
    page_contents = build_page_contents(session, request)
    dashboard = {}
    owner_ids = _build_owner_ids(page_contents)

    if len(owner_ids) != 0:
        stocks = stock_repository.find(
            {
                "owner_id__in": owner_ids,
                "status": 1,
            }
        )
        today = datetime.now().date()
        near_due_count = 0
        notify_on_count = 0
        for stock in stocks:
            if stock.notify_enabled:
                notify_on_count += 1
            if stock.expiry_date is None:
                continue
            days = (stock.expiry_date.date() - today).days
            if 0 <= days <= 3:
                near_due_count += 1

        active_tasks = habit_task_repository.find(
            {
                "owner_id__in": owner_ids,
                "is_active": True,
            }
        )
        today_str = today.strftime("%Y-%m-%d")
        today_logs = habit_task_log_repository.find(
            {
                "owner_id__in": owner_ids,
                "scheduled_date": today_str,
            }
        )
        done_today_count = len([log for log in today_logs if log.result == "done"])

        next_notify_at_text = None
        if page_contents.login_user and page_contents.login_user.linked_line_user_id:
            schedule = notification_schedule_repository.find_by_line_user_id(
                page_contents.login_user.linked_line_user_id
            )
            if schedule and schedule.next_notify_at:
                next_at = schedule.next_notify_at
                if next_at.tzinfo is None:
                    next_at = next_at.replace(tzinfo=timezone.utc)
                next_notify_at_text = next_at.astimezone(ZoneInfo("Asia/Tokyo")).strftime(
                    "%Y/%m/%d %H:%M"
                )

        dashboard = {
            "stock_total": len(stocks),
            "near_due_count": near_due_count,
            "notify_on_count": notify_on_count,
            "active_task_count": len(active_tasks),
            "done_today_count": done_today_count,
            "today_log_count": len(today_logs),
            "next_notify_at_text": next_notify_at_text,
            "line_linked": bool(
                page_contents.login_user and page_contents.login_user.linked_line_user_id
            ),
        }

    return render_template(
        'pages/index.html',
        page_contents=page_contents,
        dashboard=dashboard,
        line_add_friends_url=config.LINE_ADD_FRIENDS_URL,
    )
