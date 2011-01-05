#!/usr/bin/env python

import wsgiref.handlers
import os
import datetime

import facebook
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.ext.webapp import util

FACEBOOK_APPLICATION_ID = '118828034853760'
FACEBOOK_API_KEY = '1ce3566be4f1e3c7c37d276c8a0339c2'
FACEBOOK_SECRET_KEY = '222785905dbc92efd214cc04b7d83db7'

# DUMMY_FACEBOOK_INFO = {
#     'uid':0,
#     'name':'(Private)',
#     'first_name':'(Private)',
#     'pic_square_with_logo':'http://www.facebook.com/pics/t_silhouette.gif',
#     'affiliations':None,
#     'status':None,
#     'proxied_email':None,
# }

# Models

class User(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)

# Controllers

class BaseHandler(webapp.RequestHandler):
    @property
    def current_user(self):
        if not hasattr(self, "_current_user"):
            self._current_user = None
            cookie = facebook.get_user_from_cookie(self.request.cookies, FACEBOOK_APPLICATION_ID, FACEBOOK_SECRET_KEY)
            if cookie:
                # Store a local instance of the user data so we don't need
                # a round-trip to Facebook on every request
                user = User.get_by_key_name(cookie["uid"])
                if not user:
                    graph = facebook.GraphAPI(cookie["access_token"])
                    profile = graph.get_object("me")
                    user = User(key_name=str(profile["id"]),
                                id=str(profile["id"]),
                                name=profile["name"],
                                profile_url=profile["link"],
                                access_token=cookie["access_token"])
                    user.put()
                elif user.access_token != cookie["access_token"]:
                    user.access_token = cookie["access_token"]
                    user.put()
                self._current_user = user
        return self._current_user

class IndexHandler(BaseHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), "templates/index.html")
        args = dict(current_user=self.current_user,
                    facebook_app_id=FACEBOOK_APPLICATION_ID, facebook_api_key=FACEBOOK_API_KEY)
        self.response.out.write(template.render(path, args))

class AjaxNextEventHandler(BaseHandler):
    
    def _next_event(self):
        # get an event for the user and return it as an HTML partial
        t = str(datetime.datetime.now())
        return '<b>Next Event for user %s</b><br />%s' % (self.current_user.name, t)
    
    def get(self):
        # There must be a user logged in!
        if self.current_user is None:
            self.error(403) # access denied
        else:
            self.response.out.write(self._next_event())


class RPCMethods:
    """ Defines the methods that can be RPCed.
    NOTE: Do not allow remote callers access to private/protected "_*" methods.
    """



def main():
    application = webapp.WSGIApplication([
                        ('/', IndexHandler),
                        ('/ajax/next_event', AjaxNextEventHandler),
                    ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)
    #     util.run_wsgi_app(app)

if __name__ == "__main__":
    main()