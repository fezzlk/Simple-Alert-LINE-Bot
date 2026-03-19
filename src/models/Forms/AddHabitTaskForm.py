from wtforms import Form, IntegerField, SelectField, StringField, SubmitField, TimeField
from wtforms.validators import DataRequired, Optional


class AddHabitTaskForm(Form):
    task_name = StringField(
        label="タスク名*",
        validators=[DataRequired(message="タスク名は必須です")],
        render_kw={"class": "form-control"},
    )
    notify_time = TimeField(
        label="通知時刻*",
        validators=[DataRequired(message="通知時刻は必須です")],
        format="%H:%M",
        render_kw={"class": "form-control"},
    )
    frequency = SelectField(
        label="頻度",
        choices=[
            ("daily", "毎日"),
            ("every_other_day", "1日おき"),
            ("every_two_days", "2日おき"),
            ("weekly", "毎週"),
            ("monthly", "毎月"),
        ],
        default="daily",
        render_kw={"class": "form-select"},
    )
    notify_day_of_week = SelectField(
        label="曜日",
        choices=[
            ("", "選択してください"),
            ("0", "月曜日"),
            ("1", "火曜日"),
            ("2", "水曜日"),
            ("3", "木曜日"),
            ("4", "金曜日"),
            ("5", "土曜日"),
            ("6", "日曜日"),
        ],
        default="",
        validators=[Optional()],
        render_kw={"class": "form-select"},
    )
    notify_day_of_month = SelectField(
        label="日",
        choices=[("", "選択してください")] + [(str(i), f"{i}日") for i in range(1, 32)],
        default="",
        validators=[Optional()],
        render_kw={"class": "form-select"},
    )
    submit = SubmitField(
        label="追加",
        render_kw={"class": "btn btn-primary"},
    )
