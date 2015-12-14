import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Add(webapp2.RequestHandler):
    def get(self):
        #will just print the empty form by calling add.html
        template = JINJA_ENVIRONMENT.get_template('add.html')
        template_values = {}
        self.response.write(template.render(template_values))
    
    def post(self):
        #This will be used to add a restore to the datastore. Will be called when the user clicks on submit button on the Add Resource Page
        template = JINJA_ENVIRONMENT.get_template('index.html')
        name = self.request.get('nameInput')
        startTime = self.request.get('startInput')
        endTime = self.request.get('endInput')
        tags = self.request.get('tagsInput')
            
        
class MainPage(webapp2.RequestHandler):

    def get(self):
        #Checks for active Google session
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Sign out'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Sign in'

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/add' Add),
], debug=True)