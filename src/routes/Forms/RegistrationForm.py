from wtforms import Form, StringField, validators, SubmitField


class RegistrationForm(Form):
    web_user_email = StringField(
        label='名前',
        validators=[validators.DataRequired(message='名前は必須です')],
        render_kw={'readonly': ''},
    )
    web_user_name = StringField(
        label='メールアドレス',
        validators=[validators.DataRequired(message='メールアドレスは必須です')],
        render_kw={'readonly': ''},
    )
    submit = SubmitField('登録')
