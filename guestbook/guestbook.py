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

def getResources():
    resources = Resource.query(ancestor=resource_key()).fetch()
    return resources      

def getResourceByUser(user):
    resources = Resource.query(Resource.owner == user).fetch()
    return resources  

def getResourceById(id):
    resources = Resource.query(Resource.id == id).fetch()
    return resources      
    
class Availability(ndb.Model):
    startTime = ndb.DateTimeProperty(auto_now_add=False)
    endTime = ndb.DateTimeProperty(auto_now_add=False)

class Reservations(ndb.Model):
    owner = ndb.StringProperty(indexed=False)
    
class Resource(ndb.Model):
    name = ndb.StringProperty(indexed=True)
    availabiity = ndb.StructuredProperty(Availability, repeated=True)
    tags = ndb.StringProperty(repeated=True)
    owner = ndb.StringProperty()
    reservations = ndb.StructuredProperty(Reservations, repeated=True)
    id = ndb.StringProperty(indexed=True, required=True)
    lastReservedTime = ndb.DateTimeProperty(auto_now_add=False)
    startString = ndb.StringProperty()
    endString = ndb.StringProperty()
    dateString = ndb.StringProperty()
    
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
        dateInput = self.request.get('availDate')
        logging.info(dateInput)
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
        resource.dateString = dateInput
        resource.put()
        
        #Go back to the main page
        self.redirect('/')
        

class ResourcePage(webapp2.RequestHandler):
    def get(self):
        id = self.request.get('val')
        resource = getResourceById(id)
        template = JINJA_ENVIRONMENT.get_template('resource.html')
        template_values = {
            'resource' : resource[0],
            'owner' : resource[0].owner,
            'currUser' : users.get_current_user().email(),
            }
        self.response.write(template.render(template_values))

class UpdateResource(webapp2.RequestHandler):
    def post(self):
        resourceName = self.request.get('nameInput')
        resourceTags = self.request.get('tagsInput')
        startInput = self.request.get('startInput')
        endInput = self.request.get('endInput')
        resourceStart = datetime.datetime.strptime(startInput, '%H:%M')
        resourceEnd= datetime.datetime.strptime(endInput, '%H:%M')
        resourceDate = self.request.get('availDate')
        id = self.request.get('id')
        
        resource = getResourceById(id)
        resource[0].startString = startInput
        resource[0].endString = endInput
        resource[0].availabiity = [Availability (startTime = resourceStart, endTime = resourceEnd)]        
        resource[0].name = resourceName
        resource[0].tags = resourceTags.split(",")
        resource[0].owner = str(users.get_current_user().email())
        resource[0].reservations = []
        resource[0].id = id
        resource[0].dateString = resourceDate
        resource[0].put()
        
        #Go back to the main page
        self.redirect('/')
    
class EditResource(webapp2.RequestHandler):
    def get(self):
        id = self.request.get('val')
        resource = getResourceById(id)
        
        currUser = users.get_current_user().email()
        owner = resource[0].owner
        
        if(currUser != owner):
            template_values = {
                'error' : "You are not permitted to edit this resource"
            }
        else:  
            template_values = {
                'resourceName': resource[0].name,
                'startTime': resource[0].startString,
                'endTime': resource[0].endString,
                'tags': ', '.join(resource[0].tags),
                'uid' : resource[0].id,
                'availDate' : resource[0].dateString,
            }
        template = JINJA_ENVIRONMENT.get_template('editResource.html')
        self.response.write(template.render(template_values))
        
        
class MainPage(webapp2.RequestHandler):

    def get(self):
        #Checks for active Google session
        user = users.get_current_user()
        if user:
        
            resources = getResources()
            userResources = getResourceByUser(user.email())
            
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Sign out'
            template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'resources' : resources,
            'userresources' : userResources
            }

            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/add', Add),
    ('/resource', ResourcePage),
    ('/editResource', EditResource),
    ('/update', UpdateResource),
], debug=True)