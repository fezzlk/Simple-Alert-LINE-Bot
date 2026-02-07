from wtforms import Form, StringField, PasswordField, validators, SubmitField


class LocalLoginForm(Form):
    user_code = StringField(
        label='ユーザーコード*',
        validators=[validators.DataRequired(message='ユーザーコードは必須です')],
    )
    password = PasswordField(
        label='パスワード*',
        validators=[validators.DataRequired(message='パスワードは必須です')],
    )
    submit = SubmitField('ログイン')
