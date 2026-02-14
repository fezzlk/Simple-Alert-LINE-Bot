from wtforms import Form, StringField, SubmitField, TimeField
from wtforms.validators import DataRequired


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
    submit = SubmitField(
        label="追加",
        render_kw={"class": "btn btn-primary"},
    )
