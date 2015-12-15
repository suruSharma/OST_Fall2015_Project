import os
import urllib
import datetime
import uuid
import logging

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import db

import jinja2
import webapp2

DEFAULT_KEY = "default_key"

def resource_key():
    return ndb.Key('Resource', DEFAULT_KEY)
    
class Availability(ndb.Model):
    startTime = ndb.DateTimeProperty(auto_now_add=False)
    endTime = ndb.DateTimeProperty(auto_now_add=False)

class Reservations(ndb.Model):
    name = ndb.StringProperty(indexed=False)
    
class Resource(ndb.Model):
    name = ndb.StringProperty(indexed=False)
    availabiity = ndb.StructuredProperty(Availability, repeated=True)
    tags = ndb.StringProperty(indexed=False,repeated=True)
    owner = ndb.StringProperty(indexed=False)
    reservations = ndb.StructuredProperty(Reservations, repeated=True)
    id = ndb.StringProperty(indexed=True, required=True, default=str(uuid.uuid4()))
    lastReservedTime = ndb.DateTimeProperty(auto_now_add=False)
    startString = ndb.StringProperty(indexed=False)
    endString = ndb.StringProperty(indexed=False)
    
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
        template = JINJA_ENVIRONMENT.get_template('add.html')
        
        ##VALIDATIONS
        #Check end time is not less than start time
        error = None
        resourceName = self.request.get('nameInput')
        resourceTags = self.request.get('tagsInput')
        startInput = self.request.get('startInput')
        endInput = self.request.get('endInput')
        resourceStart = datetime.datetime.strptime(startInput, '%H:%M')
        resourceEnd= datetime.datetime.strptime(endInput, '%H:%M')
        if(resourceEnd <= resourceStart):
            error = "End time cannot be less than or equal to start time"
        
        if not(error is None):
            template_values = {
              'error': error,
              'resourceName': resourceName,
              'startTime': startInput,
              'endTime': '',
              'tags': resourceTags,
            }
            self.response.write(template.render(template_values))
            return
       
        resource = Resource(parent=resource_key())
        resource.startString = startInput
        resource.endString = endInput
        resource.availabiity = [Availability (startTime = resourceStart, endTime = resourceEnd)]        
        resource.name = resourceName
        resource.tags = resourceTags.split(",")
        resource.owner = str(users.get_current_user().email())
        resource.reservations = []
        resource.id = str(uuid.uuid4())
        resource.put()
        
        #Go back to the main page
        self.redirect('/')
        
def getResources():
    resources = Resource.query(ancestor=resource_key()).fetch()
    return resources      
            
class MainPage(webapp2.RequestHandler):

    def get(self):
        #Checks for active Google session
        user = users.get_current_user()
        if user:
        
            resources = getResources()
            
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Sign out'
            template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'resources' : resources
            }

            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/add', Add),
], debug=True)