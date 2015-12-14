import os
import urllib
import datetime
import uuid

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

def resource_key():
    currentTime = datetime.datetime.now()
    diffTime = datetime.timedelta(hours = 5)
    localTime = currentTime - diffTime
    return ndb.Key('Resource', str(localTime))
    
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
        startString = self.request.get('startInput')
        endString = self.request.get('endInput')
        resourceStart = datetime.datetime.strptime(startString, '%H:%M')
        resourceEnd= datetime.datetime.strptime(endString, '%H:%M')
        if(resourceEnd <= resourceStart):
            error = "End time cannot be less than or equal to start time"
        
        if not(error is None):
            template_values = {
              'error': error,
              'resourceName': resourceName,
              'startTime': startString,
              'endTime': '',
              'tags': resourceTags,
            }
            self.response.write(template.render(template_values))
            return
       
        resource = Resource(parent = resource_key())
        
        resource.availabiity = [Availability (startTime = resourceStart, endTime = resourceEnd)]        
        resource.name = resourceName
        resource.tags = resourceTags.split(",")
        resource.owner = str(users.get_current_user().email())
        resource.reservations = []
        resource.id = str(uuid.uuid4())
        resource.put()
        
class MainPage(webapp2.RequestHandler):

    def get(self):
        #Checks for active Google session
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Sign out'
            template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            }

            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/add', Add),
], debug=True)