from flask import Blueprint

views_blueprint = Blueprint('views_blueprint', __name__, url_prefix='/')

# register routes
from . import index  # noqa: E402,F401
from . import auth  # noqa: E402,F401
from . import stock  # noqa: E402,F401
from . import habit  # noqa: E402,F401
from . import line  # noqa: E402,F401
from . import errors  # noqa: E402,F401
