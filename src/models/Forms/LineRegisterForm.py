from wtforms import Form, StringField, validators, SubmitField


class LineRegisterForm(Form):
    web_user_name = StringField(
        label='ユーザー名*',
        validators=[validators.DataRequired(message='ユーザー名は必須です')],
    )
    submit = SubmitField('登録')
