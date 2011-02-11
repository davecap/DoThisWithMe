#!/usr/bin/env python

import wsgiref.handlers
import os
import datetime
import logging
import random

import eventful
import facebook
from django.utils import simplejson

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.ext.webapp import util
from google.appengine.api import memcache

FACEBOOK_APPLICATION_ID = '118828034853760'
FACEBOOK_API_KEY = '1ce3566be4f1e3c7c37d276c8a0339c2'
FACEBOOK_SECRET_KEY = '222785905dbc92efd214cc04b7d83db7'

logging.getLogger().setLevel(logging.DEBUG)

# Models

class User(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    picture = db.StringProperty(required=True)
    location = db.StringProperty()
    access_token = db.StringProperty()
    profile = db.ReferenceProperty(UserProfile)
    
    def get_or_create_profile(self, access_token=None):
        if access_token is none:
            access_token = self.access_token
        
        if self.profile is None:
            self.profile = UserProfile()
            self.profile.update(access_token)
            self.profile.put()
        return self.profile
                
    def get_location(self):
        if self.location:
            return self.location
        else:
            return ''

class UserEvent(db.Model):
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    friend_ids = db.StringListProperty(default=[])
    eventful_id = db.StringProperty(default=None)
    
    # TODO: async?
    def add_friend(self, user_id):
        if user_id not in self.friend_ids:
            self.friend_ids.append(user_id)
            self.put()
    
    # TODO: async?
    def remove_friend(self, user_id):
        if user_id in self.friend_ids:
            self.friend_ids.remove(user_id)
            self.put()


class UserProfile(db.Expando):
    interests = db.StringListProperty()
    music_genres = db.StringListProperty()
    book_genres = db.StringListProperty()
    book_authors = db.StringListProperty()
    movie_genres = db.StringListProperty()
    movie_directors = db.StringListProperty()
    #food_types = db.StringListProperty()
    updated = db.DateTimeProperty(auto_now=True)
    
    def update(self, access_token):
        #g = facebook.GraphAPI(access_token)
        #music = g.get_connections("me", "music")
        #books = g.get_connections("me", "books")
        #movies = g.get_connections("me", "movies")
        #interests = g.get_connections("me", "interests")
        #television = g.get_connections("me", "television")
        #albums = g.get_connections("me", "albums")
        ##likes = g.get_connections("me", "likes")
        # TODO: process interests and convert to genres
        return True

# Controllers

class BaseHandler(webapp.RequestHandler):
    @property
    def current_event(self):
        if not self.current_user:
            return None
        elif not hasattr(self, "_current_event"):
            user_event = UserEvent.get_by_key_name(self.current_user.id)
            if not user_event:
                # create a new event for a new user
                user_event = UserEvent(key_name=self.current_user.id,
                                        id=self.current_user.id)
                user_event.put()
            # TODO: expire old user events?
            self._current_event = user_event             
        return self._current_event
    
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
                    profile = graph.get_object("me", fields='id,name,link,picture,location')
                    
                    try:
                        # FB locations are in 'City, State' format
                        location = profile["location"]["name"]
                    except Exception, e:
                        logging.error(e)
                        location = None
                    
                    user = User(key_name=str(profile["id"]),
                                id=str(profile["id"]),
                                name=profile["name"],
                                profile_url=profile["link"],
                                picture=profile["picture"],
                                location=location,
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
        
        selected_friends = []
        if self.current_user and self.current_event:
            for f_id in self.current_event.friend_ids:
                u = User.get_by_key_name(f_id)
                if u:
                    selected_friends.append(u)
        
        args = dict(current_user=self.current_user, selected_friends=selected_friends, facebook_app_id=FACEBOOK_APPLICATION_ID, facebook_api_key=FACEBOOK_API_KEY)
        self.response.out.write(template.render(path, args))

class AjaxHandler(BaseHandler):
    """ Base AJAX request handler, requires logged-in user and AJAX request header """
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
        # TODO: get and set UserProfile for the current_user and friends in the friend list
        
        # # get or create the user profile by this ID
        # f_user_profile = UserProfile.get_by_key_name(f_id)
        # if f_user_profile is None:
        #     # TODO
        #     pass
        
    
        api = eventful.API('JSmFxgTgZ3kHsfTb')
        # TODO: eventful query builder
        api_data = api.call('/events/search', q='music', l=self.current_user.get_location())
        try:
            events = api_data['events']['event']
            random.shuffle(events)
            return "%s at %s" % (events[0]['title'], events[0]['venue_name'])
        except:
            return "Couldn't find any events"
        
    def process(self):
        # get an event for the user and return it as an HTML partial
        t = str(datetime.datetime.now())
        info = self.get_user_info()
        self.response.out.write('<b>Next Event for user %s</b><br />%s<br />%s' % (self.current_user.name, t, info))

class AjaxFriendListHandler(AjaxHandler):
    def process(self):
        friends = facebook.GraphAPI(self.current_user.access_token).get_connections("me", "friends")
        if friends and 'data' in friends:
            res = simplejson.dumps([ { 'value':f['id'], 'label':f['name'] } for f in friends['data'] ])
            self.response.out.write(res)

class AjaxRemoveFriendHandler(AjaxHandler):
    def process(self):
        f_id = self.request.get("id")
        self.current_event.remove_friend(f_id)
        self.response.out.write(simplejson.dumps({ "id": f_id }))
                    
class AjaxAddFriendHandler(AjaxHandler):
    def process(self):
        f_id = self.request.get("id")
        
        # get the friend's profile
        friend = User.get_by_key_name(f_id)
        if friend is None:
            profile = facebook.GraphAPI(self.current_user.access_token).get_object(f_id, fields='id,name,link,picture')
            
            friend = User(key_name=str(profile["id"]),
                        id=str(profile["id"]),
                        name=profile["name"],
                        profile_url=profile["link"],
                        picture=profile["picture"])
            friend.put()
        
        self.current_event.add_friend(f_id)
        self.response.out.write(simplejson.dumps({ "name": friend.name, "picture": friend.picture, "id": friend.id }))
       
class AjaxSetLocationHandler(AjaxHandler):
    def process(self):
        # TOD
        O process GET params: latitude, longitude, city, country, postal_code
        # set in UserProfile
        error = self.request.get("error")
        if error == '0':
            latitude = self.request.get("latitude")
            longitude = self.request.get("longitude")
            if self.current_user.get_location() != self.request.get("location"):
                self.current_user.location = self.request.get("location")
                self.current_user.put()
        self.response.out.write(simplejson.dumps({'location':self.current_user.get_location()}))
        
def main():
    application = webapp.WSGIApplication([
                        ('/', IndexHandler),
                        ('/ajax/next_event', AjaxNextEventHandler),
                        ('/ajax/friend_list', AjaxFriendListHandler),
                        ('/ajax/add_friend', AjaxAddFriendHandler),
                        ('/ajax/remove_friend', AjaxRemoveFriendHandler),
                        ('/ajax/set_location', AjaxSetLocationHandler),
                    ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)
    #     util.run_wsgi_app(app)

if __name__ == "__main__":
    main()
