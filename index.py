import os, logging, wsgiref.handlers, datetime, random, math, string, urllib, csv

from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template 
from gaesessions import get_current_session
from google.appengine.api import urlfetch



###############################################################################
###############################################################################
######################## Data Classes for Database ############################
###############################################################################
###############################################################################

class User(db.Model):
	username = 			db.StringProperty()
	firstname = 		db.StringProperty()
	lastname = 			db.StringProperty()
	usernum = 			db.IntegerProperty()
	password =			db.StringProperty()
	Module1 =			db.StringProperty()
	Module2 = 			db.StringProperty()

	

#This stores the current number of participants who have ever taken the study.
#see https://developers.google.com/appengine/docs/python/datastore/transactions
#could also use get_or_insert
#https://developers.google.com/appengine/docs/python/datastore/modelclass#Model_get_or_insert
class NumOfUsers(db.Model):
	counter = db.IntegerProperty(default=0)


#Increments NumOfUsers ensuring strong consistency in the datastore
@db.transactional
def create_or_increment_NumOfUsers():
	obj = NumOfUsers.get_by_key_name('NumOfUsers', read_policy=db.STRONG_CONSISTENCY)
	if not obj:
		obj = NumOfUsers(key_name='NumOfUsers')
	obj.counter += 1
	x=obj.counter
	obj.put()
	return(x)



###############################################################################
###############################################################################
########################### From Book Don't Touch #############################
###############################################################################
###############################################################################
# One line had to be updated for Python 2.7
#http://stackoverflow.com/questions/16004135/python-gae-assert-typedata-is-stringtype-write-argument-must-be-string
# A helper to do the rendering and to add the necessary
# variables for the _base.htm template
def doRender(handler, tname = 'index.htm', values = { }):
	temp = os.path.join(
			os.path.dirname(__file__),
			'templates/' + tname)
	if not os.path.isfile(temp):
		return False
	# Make a copy of the dictionary and add the path and session
	newval = dict(values)
	newval['path'] = handler.request.path
#   handler.session = Session()
#   if 'username' in handler.session:
#      newval['username'] = handler.session['username']

	outstr = template.render(temp, newval)
	handler.response.out.write(unicode(outstr))  #### Updated for Python 2.7
	return True


###############################################################################
###############################################################################
################################## Handlers! ##################################
###############################################################################
###############################################################################

###############################################################################
############################# Sign Up Page Handler ############################
###############################################################################

class SignupHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, 'signup.htm')

	def post(self):
		self.session = get_current_session()
		username = self.request.get('username')
		firstname = self.request.get('firstname')
		password1 = self.request.get('password1')
		password2 = self.request.get('password2')
		exists = 2

		if username == '' or firstname == '' or password1 == '' or password2 == '':
			doRender(self,
				'signupfail.htm',
				{'error': 'Please fill in all fields.'})
		# this keeps it from continuing with the rest of the handler if the "if" condition is met
			return

		# Check whether user already exists
		que = db.Query(User)
		que = que.filter('username =', username)
		results = que.fetch(limit=1)

		# If the user already exists in the datastore
		if len(results) > 0:
			doRender(self,
				'signupfail.htm',
				{'error': 'This username already exists. Please contact your professor if you need to reset your password.'})
			return

		# If the two passwords they entered do not match
		if password1 != password2:
			doRender(self,
				'signupfail.htm',
				{'error': 'Passwords do not match.'})
			return

		# Create User object in the datastore
		usernum = create_or_increment_NumOfUsers()
		newuser = User(usernum=usernum, 
			username=username,
			firstname=firstname,
			lastname=self.request.get('lastname'),
			password=password1,
			Module1="Incomplete",
			Module2="Incomplete");

		newuser.put();

		# store these variables in the session, log user in
		self.session = get_current_session() 
		self.session['usernum']    	= usernum
		self.session['username']   	= username
		self.session['firstname']	= firstname
		self.session['password']    = password1
		self.session['Module1']   	= 'Incomplete'
		self.session['Module2']  	= 'Incomplete'
		self.session['Logged_In']	= True

		doRender(self, 'menu.htm',
			{'firstname':self.session['firstname'],
			'Module1':self.session['Module1'],
			'Module2':self.session['Module2']})



###############################################################################
######################### Individual Page Handlers ############################
###############################################################################

class SingleSubjectHandler(webapp.RequestHandler):

	def get(self):
		doRender(self, "single_subject.htm")

	def post(self):
		self.session = get_current_session()
		self.session['Module1'] = 'Complete'

		# Query the datastore
		que = db.Query(User)

		# find the current user
		que = que.filter('username =', self.session['username'])
		results = que.fetch(limit=1)

		# change the datastore result for module 1
		for i in results:
			i.Module1 = self.session['Module1']
			i.put()

		logging.info('Datastore updated')

		doRender(self, 'menu.htm',
			{'firstname':self.session['firstname'],
			'Module1':self.session['Module1'],
			'Module2':self.session['Module2']})

		



class WithinSubjectHandler(webapp.RequestHandler):
	def get(self):
		self.session = get_current_session()
		if self.session['M2_Progress'] == 0:
			doRender(self, "WithinSubjectIntro.htm",
				{'progress':self.session['M2_Progress']})
		elif self.session['M2_Progress'] == 1:
			doRender(self, "WithinSubjectSim1.htm",
				{'progress':self.session['M2_Progress']})
		elif self.session['M2_Progress'] == 2:
			doRender(self, "WithinSubjectSim2.htm",
				{'progress':self.session['M2_Progress']})

	def post(self):
		logging.info("checkpoint 1")
		self.session = get_current_session()
<<<<<<< HEAD
		self.session['Module2'] = 'Complete'
		
		# Query the datastore
		que = db.Query(User)

		# find the current user
		que = que.filter('username =', self.session['username'])
		results = que.fetch(limit=1)

		# change the datastore result for module 2
		for i in results:
			i.Module2 = self.session['Module2']
			i.put()

		logging.info('Datastore updated')

		doRender(self, 'menu.htm',
			{'firstname':self.session['firstname'],
			'Module1':self.session['Module1'],
			'Module2':self.session['Module2']})	



class LineGraphTestHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, "linegraph.htm")
=======
		progress = int(self.request.get('progressinput'))
		self.session['M2_Progress'] = progress
		logging.info("Progress: "+str(progress))
		if progress == 3:
			# Record things from intro (answers to questions)
			doRender(self, "WithinSubjectSim1.htm")
		elif progress == 4:
			# Record things from sim 1 
			doRender(self, "WithinSubjectSim2.htm",
				{'progress':progress})
		# elif progress == 5:
		# 	# Record things from sim 2
		# 	doRender(self, "WithinSubjectSim1.htm",
		# 		{'progress':progress})
		# elif progress == 6:
		# 	# Record results of final quiz
		# 	doRender(self, "WithinSubjectSim1.htm",
		# 		{'progress':progress})

		# 	# Record that user completed the module
		# 	self.session['Module2'] = 'Complete'
			
		# 	# Query the datastore
		# 	que = db.Query(User)

		# 	# find the current user
		# 	que = que.filter('username =', self.session['username'])
		# 	results = que.fetch(limit=1)

		# 	# change the datastore result for module 2
		# 	for i in results:
		# 		i.Module2 = self.session['Module2']
		# 		i.put()

		# 	logging.info('Datastore updated')

		# 	doRender(self, 'menu.htm',
		# 		{'firstname':self.session['firstname'],
		# 		'Module1':self.session['Module1'],
		# 		'Module2':self.session['Module2']})	
		else:
			logging.info("something is wrong")
		
>>>>>>> edf14cea77b73b2ad8aa858b6e1728561c0c1258

		
###############################################################################
######################### Data Display Page Handler ###########################
###############################################################################

class DataHandler(webapp.RequestHandler):
	def get(self):

		doRender(self, 'datalogin.htm')


	def post(self):
		password=self.request.get('password')

		if password == " ": # just for now


			que=db.Query(User)
			que.order("usernum")
			users=que.fetch(limit=10000)

			doRender(
				self, 
				'data.htm',
				{'users':users})
		else:
			doRender(self, 'dataloginfail.htm')
 

###############################################################################
############################### Logging In and Out ############################
###############################################################################

class LoginHandler(webapp.RequestHandler):
	def get(self):
		self.session = get_current_session()

		# If they're logged in, take them to the main menu
		if 'Logged_In' in self.session:
			if self.session['Logged_In'] == True:
				doRender(self, 'menu.htm',
					{'firstname':self.session['firstname'],
					'Module1':self.session['Module1'],
					'Module2':self.session['Module2']})
			else:
				doRender(self, 'login.htm')
		# If they aren't, take them to the login page
		else:
			self.session['Logged_In'] = False
			doRender(self, 'login.htm')

	def post(self):
		self.session = get_current_session()
		
		username = self.request.get('username')
		password = self.request.get('password')
		
		# Check whether user already exists
		que = db.Query(User)
		que = que.filter('username =', username)
		results = que.fetch(limit=1)

		# If user does not exist
		if len(results) == 0:
			doRender(self,
				'loginfailed.htm',
				{'error': 'This username does not exist'})
			return

		# Check if password matches password entry in datastore
		que = que.filter('password =', password)
		results = que.fetch(limit=1)

		# If password mismatch
		if len(results) == 0:
			doRender(self,
				'loginfailed.htm',
				{'error': 'Incorrect password'})
			return


		# i is a list object (basically a row of data) in the datastore. This loop saves each relevant piece of info from our query into the session.
		for i in results:
			self.session['username'] = i.username
			self.session['password'] = i.password
			self.session['firstname'] = i.firstname
			self.session['usernum'] = i.usernum
			self.session['Module1'] = i.Module1
			self.session['Module2'] = i.Module2
			self.session['M2_Progress'] = 0


		
		doRender(self,'menu.htm',
			{'firstname':self.session['firstname'],
			'Module1':self.session['Module1'],
			'Module2':self.session['Module2']})


class LogoutHandler(webapp.RequestHandler):
	
	def get(self):	
		self.session = get_current_session()
		self.session['Logged_In'] = False	
		
		# kill all the session stuff that would identify them (username, password, etc)
		sessionlist = ['usernum', 'username', 'password', 'Module1', 'Module2', 'Logged_In']

		for i in sessionlist:
			if i in self.session:
				self.session.__delitem__(i)

		# Send them back to the login page
		doRender(self, 'login.htm')


		
###############################################################################
############################### MainAppLoop ###################################
###############################################################################

application = webapp.WSGIApplication([
	('/data', DataHandler),
	('/logout', LogoutHandler),
	('/login', LoginHandler),
	('/signup', SignupHandler),
	('/SingleSubject', SingleSubjectHandler),
	('/WithinSubject', WithinSubjectHandler),
	('/LineGraphTest', LineGraphTestHandler),
	('/.*',  LoginHandler)],  #default page
	debug=True)

def main():
		run_wsgi_app(application)

if __name__ == '__main__':
	main()

