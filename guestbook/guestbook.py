import os
import urllib
import datetime
import uuid
import logging

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import db
from google.appengine.api import mail

import jinja2
import webapp2

DEFAULT_KEY = "default_key"
DEFAULT_RESERVATION_KEY = "default_reservation_key"

def resource_key():
    return ndb.Key('Resource', DEFAULT_KEY)

def reservation_key(email):
    return ndb.Key('Reservations', email)

def getResources():
    resources = Resource.query(ancestor=resource_key()).order(-Resource.lastReservedTime).fetch()
    return resources      

def getResourceByUser(user):
    resources = Resource.query(Resource.owner == user).order(-Resource.lastReservedTime).fetch()
    return resources  

def getReservationsForUser(user):
    reservations_query = Reservations.query(ancestor=reservation_key(user))
    reservations = reservations_query.order(Reservations.startTime).fetch()
    return reservations

def deleteReservation(deleteId):
    reservations = Reservations.query(Reservations.uid == deleteId).fetch()
    for r in reservations:
        r.key.delete()
    
def getResourceById(id):
    resources = Resource.query(Resource.id == id).fetch()
    return resources   

def getResourcesByTag(tag):
    resources = getResources()
    result = []
    for r in resources:
        print r.tags
        if tag in r.tags:
            result.append(r)
    return result
    
def getReservationsById(id):
    reservations_query = Reservations.query(Reservations.resourceId == id)
    reservations = reservations_query.order(Reservations.startTime).fetch()
    return reservations

def getEndTime(reservationInput, durationInput):
    hh = int(durationInput) / 60
    mm = int(durationInput) % 60
    st = reservationInput.split(":")
    end = datetime.time(int(st[0])+hh, int(st[1])+mm, 0)
    return end
    
def slotIsFree(reservationInput, durationInput, id):
    existingReservations = getReservationsById(id)
    
    st = reservationInput.split(":")
    rStart = datetime.time(int(st[0]), int(st[1]), 0)
    rEnd = getEndTime(reservationInput, durationInput)
    logging.info(rStart)
    logging.info(rEnd)
    
    for r in existingReservations:
        resverStart = r.startTime
        reservEnd = r.startTime + datetime.timedelta(minutes = r.duration)
        
        start = datetime.time(resverStart.hour, resverStart.minute, 0)
        end = datetime.time(reservEnd.hour, reservEnd.minute, 0)
        
        if rStart == start:
            return False
        elif (rStart < start and rEnd > start) or (rStart > start and rStart < end):
            return False
        #compare the incoming reservation start time and reservation duration
        
    return True
    
class Availability(ndb.Model):
    startTime = ndb.DateTimeProperty(auto_now_add=False)
    endTime = ndb.DateTimeProperty(auto_now_add=False)

class Reservations(ndb.Model):
    owner = ndb.StringProperty(indexed=False)
    resourceId = ndb.StringProperty(indexed=True, required=True)
    resourceName = ndb.StringProperty(indexed=False)
    startTime = ndb.DateTimeProperty(auto_now_add=False)
    duration = ndb.IntegerProperty()
    strignStart = ndb.StringProperty()
    uid = ndb.StringProperty(indexed=True, required=True)
    
class Resource(ndb.Model):
    name = ndb.StringProperty(indexed=True)
    availabiity = ndb.StructuredProperty(Availability, repeated=True)
    tags = ndb.StringProperty(repeated=True)
    owner = ndb.StringProperty()
    id = ndb.StringProperty(indexed=True, required=True)
    lastReservedTime = ndb.DateTimeProperty(auto_now_add=False)
    startString = ndb.StringProperty()
    endString = ndb.StringProperty()
    dateString = ndb.StringProperty()
    count = ndb.IntegerProperty()
    
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
       
        tags = resourceTags.split(",")
        rt = []
        for t in tags:
            rt.append(t.strip())
            
        resource = Resource(parent=resource_key())
        resource.startString = startInput
        resource.endString = endInput
        resource.availabiity = [Availability (startTime = resourceStart, endTime = resourceEnd)]        
        resource.name = resourceName
        resource.tags = rt
        resource.owner = str(users.get_current_user().email())
        resource.id = str(uuid.uuid4())
        resource.dateString = dateInput
        resource.count = 0
        resource.put()
        
        #Go back to the main page
        self.redirect('/')
        

class ResourcePage(webapp2.RequestHandler):
    def get(self):
        id = self.request.get('val')
        resource = getResourceById(id)
        reservations = getReservationsById(id)
        
        template = JINJA_ENVIRONMENT.get_template('resource.html')
        template_values = {
            'resource' : resource[0],
            'owner' : resource[0].owner,
            'currUser' : users.get_current_user().email(),
            'reservations' : reservations,
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
        resource[0].id = id
        resource[0].dateString = resourceDate
        resource[0].put()
        
        #Go back to the main page
        self.redirect('/')

class Reserve(webapp2.RequestHandler):
    def post(self):
        id = self.request.get('id')
        startInput = self.request.get('startInput')
        durationInput = int(self.request.get('duration'))
        user = users.get_current_user().email()
        reservationStart = datetime.datetime.strptime(startInput, '%H:%M')
         
        resource = getResourceById(id)
        
        #Check if this is a valid time to reserve
        if(slotIsFree(startInput, durationInput, id)):
            logging.info("Free to reserve")
            reservation = Reservations(parent=reservation_key(user))
            reservation.owner = user
            reservation.resourceId = id
            reservation.startTime = reservationStart
            reservation.duration = durationInput
            reservation.resourceName = resource[0].name
            reservation.strignStart = startInput
            reservation.uid = str(uuid.uuid4())
            reservation.put()
            
            #Update the count and last reserved time in the resource model
            
            currCount = resource[0].count
            resource[0].count = currCount + 1
            resource[0].lastReservedTime = datetime.datetime.now() - datetime.timedelta(hours = 5)
            
            resource[0].put()
            
            #sendMail(user, resource[0].name)
            #mail the user
            #Go back to the main page
            self.redirect('/')
        else:
            logging.info("Cannot reserve")
            #should write error back into same page

        
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

class Tag(webapp2.RequestHandler):
    def get(self):
       tag = self.request.get('val')
       resources = getResourcesByTag(tag)
       template = JINJA_ENVIRONMENT.get_template('tags.html')
       template_values = {
                'resources': resources,
                'tag' : tag
            }
       self.response.write(template.render(template_values))
       
class DeleteReservation(webapp2.RequestHandler):
    def post(self):
        reservationId = self.request.get('val')
        deleteReservation(reservationId)
        resourceId = self.request.get('resourceId')
        resource = getResourceById(resourceId)
        count = resource[0].count
        resource[0].count = count - 1
        resource[0].put()
        self.redirect('/resource?val='+resourceId)
        
class AddReservation(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('addReservation.html')
        id = self.request.get('val')
        resource = getResourceById(id);
        logging.info(id)
        template_values = {
            'id' : id,
            'availDate' : resource[0].dateString,
            'resourceName' : resource[0].name,
            'startTime': resource[0].startString,
            'endTime': resource[0].endString,
        }
        self.response.write(template.render(template_values))
        
class MainPage(webapp2.RequestHandler):

    def get(self):
        #Checks for active Google session
        user = users.get_current_user()
        if user:
            resources = getResources()
            userResources = getResourceByUser(user.email())
            reservations = getReservationsForUser(user.email())
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Sign out'
            template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'resources' : resources,
            'userresources' : userResources,
            'reservations' : reservations
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
    ('/addReservation', AddReservation),
    ('/reserve', Reserve),
    ('/tag', Tag),
    ('/deleteReservation', DeleteReservation)
    
], debug=True)