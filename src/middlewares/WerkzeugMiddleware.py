import logging

from werkzeug.wrappers import Request

logger = logging.getLogger(__name__)


class WerkzeugMiddleware():
    '''
    Simple WSGI middleware
    '''

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = Request(environ)
        logger.debug('WerkzeugMiddleware: %s %s', request.method, request.path)
        return self.app(environ, start_response)
