from werkzeug.wrappers import Request


class WerkzeugMiddleware():
    '''
    Simple WSGI middleware
    '''

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = Request(environ)
        print('call WerkzeugMiddleware')
        print(request)
        print(start_response)
        return self.app(environ, start_response)
