from functools import wraps
from flask import request, redirect, url_for, session


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print('call login required')
        if 'login_email' not in session:
            return redirect(url_for('views_blueprint.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
