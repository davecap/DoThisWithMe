"""
eventful

A Python interface to the Eventful API.

"""

__author__    = "Edward O'Connor <ted@eventful.com>"
__copyright__ = "Copyright 2005, 2006 Eventful Inc."
__license__   = "MIT"

import logging
logging.getLogger().setLevel(logging.DEBUG)

import md5
import urllib

# Find a JSON parser
try:
    import json
    _parse_json = lambda s: json.loads(s)
except ImportError:
    try:
        import simplejson
        _parse_json = lambda s: simplejson.loads(s)
    except ImportError:
        # For Google AppEngine
        from django.utils import simplejson
        _parse_json = lambda s: simplejson.loads(s)

__all__ = ['APIError', 'API']

class APIError(Exception):
    pass

class API:
    def __init__(self, app_key, server='api.eventful.com', cache=None):
        """Create a new Eventful API client instance.
If you don't have an application key, you can request one:
    http://api.eventful.com/keys/"""
        self.app_key = app_key
        self.server = server

    def call(self, method, **args):
        "Call the Eventful API's METHOD with ARGS."
        # Build up the request
        args['app_key'] = self.app_key
        if hasattr(self, 'user_key'):
            args['user'] = self.user
            args['user_key'] = self.user_key
        args = urllib.urlencode(args)
        url = "http://%s/json/%s?%s" % (self.server, method, args)
        
        file = urllib.urlopen(url)
        try:
            return _parse_json(file.read())
        finally:
            file.close()
        if response.get("error"):
            raise APIError("Unable to parse API response! Error: %s. %s" % (response["error"]["type"], response["error"]["message"]))
        
        return []
        
        # Handle the response
        # status = int(response['status'])
        # if status == 200:
        #     try:
        #         return simplejson.loads(content)
        #     except ValueError:
        #         raise APIError("Unable to parse API response!")
        # elif status == 404:
        #     raise APIError("Method not found: %s" % method)
        # else:
        #     raise APIError("Non-200 HTTP response status: %s" % response['status'])

    def login(self, user, password):
        "Login to the Eventful API as USER with PASSWORD."
        nonce = self.call('/users/login')['nonce']
        response = md5.new(nonce + ':'
                           + md5.new(password).hexdigest()).hexdigest()
        login = self.call('/users/login', user=user, nonce=nonce,
                          response=response)
        self.user_key = login['user_key']
        self.user = user
        return user
