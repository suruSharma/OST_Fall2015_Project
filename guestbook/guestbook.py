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

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

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
    return removeOldReservations(reservations)

def removeOldReservations(reservations):
    current_date = datetime.datetime.now() - datetime.timedelta(hours = 5)
    finalReservations = []
    
    for r in reservations : 
        rDate = r.date
        end = getEndTime(r.strignStart, r.duration)
        r_day = rDate.split("-")[2]
        r_month = rDate.split("-")[1]
        r_year = rDate.split("-")[0]
        r_hour = end.hour
        r_minutes = end.minute
        endDate = datetime.datetime(int(r_year), int(r_month), int(r_day), int(r_hour), int(r_minutes))
        if current_date > endDate :
            continue
        else:
            finalReservations.append(r)
            
    finalReservations.sort(customSort)    
    return finalReservations
    
def customSort(r1,r2):
    rStart1 = r1.startTime
    rDate1 = r1.date
    r1_day = rDate1.split("-")[2]
    r1_month = rDate1.split("-")[1]
    r1_year = rDate1.split("-")[0]
    rStart1 = rStart1.replace(day=int(r1_day), month=int(r1_month), year=int(r1_year))
    
    rStart2 = r2.startTime
    rDate2 = r2.date
    r2_day = rDate2.split("-")[2]
    r2_month = rDate2.split("-")[1]
    r2_year = rDate2.split("-")[0]
    rStart2 = rStart2.replace(day=int(r2_day), month=int(r2_month), year=int(r2_year))
    
    if rStart1 > rStart2:
        return 1
    if rStart1 == rStart2:
        return 0
    if rStart1 < rStart2:
        return -1
    
def deleteReservation(deleteId):
    reservations = Reservations.query(Reservations.uid == deleteId).fetch()
    for r in reservations:
        r.key.delete()
        
def deleteReservationByResourceId(resourceId):
    reservations = getReservationsById(resourceId)
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
    return removeOldReservations(reservations)

def getEndTime(reservationInput, durationInput):
    st = reservationInput.split(":")
    hh = int(durationInput) / 60
    mm = int(durationInput) % 60

    finalhh = int(st[0])+hh
    finalmm = int(st[1])+mm
    
    if(finalmm > 60):
        finalhh = (finalmm / 60) + finalhh
        finalmm = finalmm % 60
        
    end = datetime.time(int(finalhh), int(finalmm), 0)
    return end
    
def slotIsFree(reservationInput, durationInput, id, dateString):
    existingReservations = getReservationsById(id)
    
    current = datetime.datetime.now() - datetime.timedelta(hours = 5)
    currTime = datetime.time(int(current.hour), int(current.minute), int(current.second))    
    
    st = reservationInput.split(":")
    rStart = datetime.time(int(st[0]), int(st[1]), 0)
    rEnd = getEndTime(reservationInput, durationInput)
    
    d = dateString.split("-")
    actualEnd = current
    actualEnd = actualEnd.replace(day=int(d[2]), month=int(d[1]), year=int(d[0]), hour = rEnd.hour, minute = rEnd.minute, second = 0)
    actualStart = current
    actualStart = actualStart.replace(day=int(d[2]), month=int(d[1]), year=int(d[0]), hour = int(st[0]), minute = int(st[1]), second = 0)
    
    if(actualEnd < current):
        logging.info("Inside 1")
        return False
        
    for r in existingReservations:
        resverStart = r.startTime
        reservEnd = r.startTime + datetime.timedelta(minutes = r.duration)
        
        start = datetime.time(resverStart.hour, resverStart.minute, 0)
        end = datetime.time(reservEnd.hour, reservEnd.minute, 0)
        
        reservationStart = actualStart
        reservationStart = reservationStart.replace(hour = resverStart.hour, minute = resverStart.minute)

        reservationEnd = actualStart
        reservationEnd = reservationEnd.replace(hour = reservEnd.hour, minute = reservEnd.minute)
        
        if actualStart == reservationStart:
            logging.info("Inside 2")
            return False
        elif (actualStart < reservationStart and actualEnd > reservationStart) or (actualStart > reservationStart and actualStart < reservationEnd):
            logging.info("Inside 3")
            return False
        #compare the incoming reservation start time and reservation duration
        
    return True

def sendMail(resource, reservation):
    mail.send_mail(sender="sss665@nyu.edu",
                    to=reservation.owner,
                    subject=resource.name+" is reserved for you",
                    body = """
                    Hi """+reservation.owner+"""
                        You have reserved """ + resource.name + """ on """+reservation.date+""" from """+reservation.strignStart+""" for """+str(reservation.duration)+""" minute/s """)
                    
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
    date = ndb.StringProperty()
    
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
        deleteReservationByResourceId(id)
        resource = getResourceById(id)
        resource[0].startString = startInput
        resource[0].endString = endInput
        resource[0].availabiity = [Availability (startTime = resourceStart, endTime = resourceEnd)]        
        resource[0].name = resourceName
        resource[0].tags = resourceTags.split(",")
        resource[0].owner = str(users.get_current_user().email())
        resource[0].id = id
        resource[0].dateString = resourceDate
        resource[0].count = 0
        resource[0].put()
        
        #Go back to the main page
        self.redirect('/')

class Reserve(webapp2.RequestHandler):
    def post(self):
        id = self.request.get('id')
        dateString = self.request.get('dateString')
        startInput = self.request.get('startInput')
        durationInput = int(self.request.get('duration'))
        user = users.get_current_user().email()
        reservationStart = datetime.datetime.strptime(startInput, '%H:%M')
         
        resource = getResourceById(id)
        
        #Check if this is a valid time to reserve
        if(slotIsFree(startInput, durationInput, id, dateString)):
            reservation = Reservations(parent=reservation_key(user))
            reservation.owner = user
            reservation.resourceId = id
            reservation.startTime = reservationStart
            reservation.duration = durationInput
            reservation.resourceName = resource[0].name
            reservation.strignStart = startInput
            reservation.uid = str(uuid.uuid4())
            reservation.date = resource[0].dateString
            reservation.put()
            
            #Update the count and last reserved time in the resource model
            
            currCount = resource[0].count
            resource[0].count = currCount + 1
            resource[0].lastReservedTime = datetime.datetime.now() - datetime.timedelta(hours = 5)
            
            resource[0].put()
            
            sendMail(resource[0], reservation)
            #mail the user
            #Go back to the main page
            self.redirect('/')
        else:
            template = JINJA_ENVIRONMENT.get_template('addReservation.html')
            template_values = {
                'error' : "The selected duration is not available for this resource. Select another time slot.",
                'id' : id,
                'availDate' : resource[0].dateString,
                'resourceName' : resource[0].name,
                'startTime': resource[0].startString,
                'endTime': resource[0].endString,
            }
            self.response.write(template.render(template_values))

        
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
        self.redirect('/')
        
class AddReservation(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('addReservation.html')
        id = self.request.get('val')
        resource = getResourceById(id);
        template_values = {
            'id' : id,
            'availDate' : resource[0].dateString,
            'resourceName' : resource[0].name,
            'startTime': resource[0].startString,
            'endTime': resource[0].endString,
        }
        self.response.write(template.render(template_values))

class UserPage(webapp2.RequestHandler):
    def get(self):
        user = self.request.get('val')
        userResources = getResourceByUser(user)
        reservations = getReservationsForUser(user)
        template_values = {
            'user' : user,
            'userPage' : "yes",
            'userresources' : userResources,
            'reservations' : reservations
        }
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
        
class GenerateRSSFeed(webapp2.RequestHandler):
    def get(self):
        id = self.request.get('val')
        resource = getResourceById(id)
        reservations = getReservationsById(id)
        rssFeed = "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n"
        rssFeed = rssFeed + "<rss version=\"2.0\">\n\n"
        rssFeed = rssFeed + "<channel>\n"
        rssFeed = rssFeed + "\t<title>"+str(resource[0].name)+"</title>\n"
        rssFeed = rssFeed + "\t<link>/resource?val="+resource[0].id+"</link>\n"
        rssFeed = rssFeed + "\t<description>"+str(resource[0].name)+" is available on "+resource[0].dateString+" from "+resource[0].startString+" to "+resource[0].endString+"</description>\n"
        
        for r in reservations:
            rssFeed = rssFeed + "\t<item>\n"
            rssFeed = rssFeed + "\t\t<title>Reservation made by "+r.owner+"</title>\n"
            rssFeed = rssFeed + "\t\t<link>/resource?val="+resource[0].id+"</link>\n"
            rssFeed = rssFeed + "\t\t<description>Reserved from "+r.strignStart+" for "+str(r.duration)+" minute/s</description>\n"
            rssFeed = rssFeed + "\t</item>\n"
        
        rssFeed = rssFeed + "</channel>\n"
        rssFeed = rssFeed + "</rss>"
        
        template = JINJA_ENVIRONMENT.get_template('rssFeed.html')
        template_values = {
            'rssFeed' : rssFeed,
            'name' : resource[0].name
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
            url_linktext = 'SIGN OUT'
            template_values = {
            'user': user,
            'url': url,
            'userPage' : "no",
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
    ('/deleteReservation', DeleteReservation),
    ('/ownerInfo', UserPage),
    ('/rssfeed', GenerateRSSFeed)
    
], debug=True)