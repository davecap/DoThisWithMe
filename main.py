#!/usr/bin/env python

import wsgiref.handlers
import os
import datetime

import facebook
from django.utils import simplejson

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
        args = dict(current_user=self.current_user, facebook_app_id=FACEBOOK_APPLICATION_ID, facebook_api_key=FACEBOOK_API_KEY)
        self.response.out.write(template.render(path, args))

class AjaxHandler(BaseHandler):
    def process(self):
        raise NotImplementedError()
    
    def get(self):
        # must be logged in
        if self.current_user is None:
            return self.error(403)
        # must be ajax request
        if 'X-Requested-With' not in self.request.headers.keys() or self.request.headers['X-Requested-With'] != 'XMLHttpRequest':
            return self.error(403)
        self.process()

class AjaxNextEventHandler(AjaxHandler):
    def get_user_info(self):
        g = facebook.GraphAPI(self.current_user.access_token)
        interests = g.get_connections("me", "interests")
        music = g.get_connections("me", "music")
        books = g.get_connections("me", "books")
        movies = g.get_connections("me", "movies")
        television = g.get_connections("me", "television")
        albums = g.get_connections("me", "albums")
        #likes = g.get_connections("me", "likes")
        return '%s<br />%s<br />%s<br />%s<br />%s<br />%s<br />' % (interests, music, books, movies, albums, television)
        
    def process(self):
        # get an event for the user and return it as an HTML partial
        t = str(datetime.datetime.now())
        info = self.get_user_info()
        self.response.out.write('<b>Next Event for user %s</b><br />%s<br />%s' % (self.current_user.name, t, info))

class AjaxFriendListHandler(AjaxHandler):
    def process(self):
        # TODO: add exception handling and proper logging of errors
        friends = facebook.GraphAPI(self.current_user.access_token).get_connections("me", "friends")
        if friends and 'data' in friends:
            res = simplejson.dumps([ { 'value':f['id'], 'label':f['name'] } for f in friends['data'] ])
            self.response.out.write(res)

class AjaxAddFriendHandler(AjaxHandler):
    def process(self):
        # TODO: add exception handling and proper logging of errors
        friend = facebook.GraphAPI(self.current_user.access_token).get_object(self.request.get("id"),fields='id,name,picture')
        self.response.out.write(simplejson.dumps({ "name": friend["name"], "picture": friend["picture"] }))
               
def main():
    application = webapp.WSGIApplication([
                        ('/', IndexHandler),
                        ('/ajax/next_event', AjaxNextEventHandler),
                        ('/ajax/friend_list', AjaxFriendListHandler),
                        ('/ajax/add_friend', AjaxAddFriendHandler),
                    ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)
    #     util.run_wsgi_app(app)

if __name__ == "__main__":
    main()
