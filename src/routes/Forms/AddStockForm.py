from wtforms import Form, StringField, validators, SubmitField, DateField


class AddStockForm(Form):
    item_name = StringField(
        label='アイテム名*',
        validators=[validators.DataRequired(message='アイテム名は必須です')],
        render_kw={'class': 'form-control'},
    )
    expiry_date = DateField(
        label='期限',
        render_kw={'class': 'form-control'},
    )
    submit = SubmitField(
        label='追加',
        render_kw={'class': 'btn btn-primary'},
    )
