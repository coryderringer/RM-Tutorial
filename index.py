import os, logging, wsgiref.handlers, datetime, random, math, string, urllib, csv, json

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
	# password =			db.StringProperty()
	Module1 =			db.StringProperty()
	Module2 = 			db.StringProperty()
	Module3 = 			db.StringProperty()
	WSAnswer1 = 		db.StringProperty()
	WSAnswer2 = 		db.StringProperty()
	WSAnswer3 = 		db.StringProperty()
	COEAnswer1 =		db.StringProperty()
	COEAnswer2 =		db.StringProperty()
	COEAnswer3 =		db.IntegerProperty()
	COEAnswer4 =		db.IntegerProperty()
	COEAnswer5 =		db.IntegerProperty()
	term = 				db.StringProperty()
	instructor = 		db.StringProperty()
	PFEAnswer1 =		db.StringProperty()
	PFEAnswer2 =		db.StringProperty()
	PFEAnswer3 =		db.IntegerProperty()
	PFEAnswer4 =		db.IntegerProperty()
	# PFEAnswer5 =		db.IntegerProperty()
	numberOfGuesses = 	db.IntegerProperty()
	numberOfSimulations = db.IntegerProperty()
	numberOfSimulations2 = db.IntegerProperty()
	QuizResults = 		db.ListProperty(str)
	

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

################################################################################
################################################################################
################ Function to read data to show participants ####################
################################################################################
################################################################################

def readData(module,stimuli):
	if module=='test':
		f = open('test.csv', 'rU')
	
	data = csv.reader(f)
	data = list(data)

	condition = [0]*len(data)
	x = [0]*len(data)
	y = [0]*len(data)
	coord = [0,0]*len(data)

	for i in range(0,len(data)):
		condition[i] = int(data[i][0])
		x[i] = float(data[i][1])
		y[i] = float(data[i][2])

	return condition, x, y

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
		instructor = self.request.get('instructor')

		logging.info('INSTRUCTOR: '+instructor)
		
		# password1 = self.request.get('password1')
		# password2 = self.request.get('password2')
		exists = 2

		# if username == '' or firstname == '':# or password1 == '' or password2 == '':
		# 	doRender(self,
		# 		'signupfail.htm',
		# 		{'error': 'Please fill in all fields.'})
		# # this keeps it from continuing with the rest of the handler if the "if" condition is met
		# 	return

		# Check whether user already exists
		que = db.Query(User)
		que = que.filter('username =', username)
		results = que.fetch(limit=1)

		# If the user already exists in the datastore
		# if len(results) > 0:
		# 	doRender(self,
		# 		'signupfail.htm',
		# 		{'error': 'This username already exists. Please contact your professor if you need to reset your password.'})
		# 	return

		# If the two passwords they entered do not match
		# if password1 != password2:
		# 	doRender(self,
		# 		'signupfail.htm',
		# 		{'error': 'Passwords do not match.'})
		# 	return

		# Create User object in the datastore
		usernum = create_or_increment_NumOfUsers()
		newuser = User(usernum=usernum, 
			username=username,
			firstname=firstname,
			lastname=self.request.get('lastname'),
			# note: this is the manual input for term. Doesn't make sense at this point to have them do this themselves since it's all for Spring 2016
			term='Spring 2016',
			
			instructor=instructor,
			# password=password1,
			Module1="Incomplete",
			Module2="Incomplete",
			Module3="Incomplete");

		newuser.put();

		# store these variables in the session, log user in
		self.session = get_current_session() 
		self.session['usernum']    	= usernum
		self.session['username']   	= username
		self.session['firstname']	= firstname
		# self.session['password']    = password1
		self.session['Module1']   	= 'Incomplete'
		self.session['Module2']  	= 'Incomplete'
		self.session['Module3']  	= 'Incomplete'
		self.session['Logged_In']	= True
		self.session['M1_Progress'] = 0
		self.session['M2_Progress'] = 0
		self.session['M3_Progress'] = 0

		doRender(self, 'menu.htm',
			{'firstname':self.session['firstname'],
			'Module1':self.session['Module1'],
			'Module2':self.session['Module2'],
			'Module3':self.session['Module3']})



###############################################################################
######################### Individual Page Handlers ############################
###############################################################################

class CarryoverEffectsHandler(webapp.RequestHandler):

	def get(self):
		self.session = get_current_session()
		if self.session['M1_Progress'] == 0:
			doRender(self, "CarryoverEffectsIntro.htm",
				{'progress':self.session['M1_Progress']})

	def post(self):
		logging.info("checkpoint 1")
		self.session = get_current_session()

		M1_Progress = int(self.request.get('progressinput'))
		self.session['M1_Progress'] = M1_Progress
		logging.info("Progress: "+str(M1_Progress))
		
		if M1_Progress == 1:
			self.session['COEAnswer1'] = self.request.get('Q1')

			doRender(self, "CarryoverEffects1.htm",
				{'progress':self.session['M1_Progress']})

		elif M1_Progress == 2:
			self.session['COEAnswer2'] = self.request.get('Q2')

			doRender(self, "CarryoverEffects2.htm",
				{'progress':self.session['M1_Progress']})

		elif M1_Progress == 3:
			# self.session['COEAnswer3'] = self.request.get('Q3')

			doRender(self, "CarryoverEffects3.htm",
				{'progress':self.session['M1_Progress']})

		elif M1_Progress == 4:
			doRender(self, "CarryoverEffectsQuiz.htm",
				{'progress':self.session['M1_Progress']})

		elif M1_Progress == 5:
			COEAnswer3 = int(self.request.get('Question1'))
			COEAnswer4 = int(self.request.get('Question2'))
			COEAnswer5 = int(self.request.get('Question3'))

			# Record that user completed the module
			self.session['Module1'] = 'Complete'

			# Query the datastore
			que = db.Query(User)

			# find the current user
			que = que.filter('username =', self.session['username'])
			results = que.fetch(limit=1)

			# change the datastore result for module 1
			for i in results:
				i.COEAnswer1 = self.session['COEAnswer1']
				i.COEAnswer2 = self.session['COEAnswer2']
				i.COEAnswer3 = COEAnswer3
				i.COEAnswer4 = COEAnswer4
				i.COEAnswer5 = COEAnswer5
				i.Module1 = self.session['Module1']
				i.put()

			logging.info('Datastore updated')

			self.session['M1_Progress'] = 0
			doRender(self, "FinishCarryoverEffects.htm")
		else:
			logging.info("something is wrong")



class PracticeFatigueEffectsHandler(webapp.RequestHandler):

	def get(self):
		self.session = get_current_session()
		if self.session['M3_Progress'] == 0:
			doRender(self, "PracticeFatigueEffectsIntro.htm",
				{'progress':self.session['M3_Progress']})

	def post(self):
		logging.info("checkpoint 1")
		self.session = get_current_session()

		M1_Progress = int(self.request.get('progressinput'))
		self.session['M3_Progress'] = M1_Progress
		logging.info("Progress: "+str(M1_Progress))
		
		if M1_Progress == 1:
			self.session['PFEAnswer1'] = self.request.get('Q1')

			doRender(self, "PracticeFatigueEffects1.htm",
				{'progress':self.session['M3_Progress']})

		elif M1_Progress == 2:
			self.session['PFEAnswer2'] = self.request.get('Q2')

			doRender(self, "PracticeFatigueEffects2.htm",
				{'progress':self.session['M3_Progress']})

		elif M1_Progress == 3:
			doRender(self, "PracticeFatigueEffectsQuiz.htm",
				{'progress':self.session['M3_Progress']})

		elif M1_Progress == 4:
		# 	doRender(self, "CarryoverEffectsQuiz.htm",
		# 		{'progress':self.session['M1_Progress']})

		# elif M1_Progress == 5:
			PFEAnswer3 = int(self.request.get('Question1'))
			# PFEAnswer4 = int(self.request.get('Question2'))
			PFEAnswer5 = int(self.request.get('Question3'))

			# Record that user completed the module
			self.session['Module3'] = 'Complete'

			# Query the datastore
			que = db.Query(User)

			# find the current user
			que = que.filter('username =', self.session['username'])
			results = que.fetch(limit=1)

			# change the datastore result for module 1
			for i in results:
				i.PFEAnswer1 = self.session['PFEAnswer1']
				i.PFEAnswer2 = self.session['PFEAnswer2']
				# i.COEAnswer3 = self.session['COEAnswer3']
				i.PFEAnswer3 = PFEAnswer3
				i.PFEAnswer4 = PFEAnswer5
				# i.PFEAnswer5 = PFEAnswer5
				i.Module3 = self.session['Module3']
				i.put()

			logging.info('Datastore updated')

			self.session['M3_Progress'] = 0
			doRender(self, "FinishPracticeFatigueEffects.htm")
		else:
			logging.info("something is wrong")


class WithinSubjectHandler(webapp.RequestHandler):
	def get(self):
		self.session = get_current_session()
		if self.session['M2_Progress'] == 0:
			doRender(self, "WithinSubjectIntro.htm",
				{'progress':self.session['M2_Progress'],
				'introProgress':0})


	def post(self):
		logging.info("checkpoint 1")
		self.session = get_current_session()
		direction = self.request.get('directioninput')

		M2_Progress = int(self.request.get('progressinput'))
		self.session['M2_Progress'] = M2_Progress
		logging.info("Progress: "+str(M2_Progress))

		if M2_Progress == 0:
			doRender(self, "WithinSubjectIntro.htm",
				{'progress':self.session['M2_Progress'],
				'introProgress':3})

		elif M2_Progress == 1:
			if direction == 'forward':

				# Record things from intro (answers to questions)
				self.session['WSAnswer1'] = self.request.get('Q1')
				self.session['WSAnswer2'] = self.request.get('Q2')
				self.session['numberOfGuesses'] = int(self.request.get('guessesinput'))

				pValues1 = [[0,0,0,0]] * 50
				sigTally1 = [[0,0,0,0]] * 50
				
				f = open('pValues1.csv', 'rU')
				mycsv = csv.reader(f)
				mycsv = list(mycsv)   

				for x in range(0,50):
					pValues1[x] = [float(mycsv[x][0]), float(mycsv[x][1]), float(mycsv[x][2]), float(mycsv[x][3])]
					sigTally1[x] = [int(mycsv[x][4]), int(mycsv[x][5]), int(mycsv[x][6]), int(mycsv[x][7])]

				self.session['pValues1'] = pValues1
				self.session['sigTally1'] = sigTally1

				doRender(self, "WithinSubjectSim1.htm",
					{'progress':self.session['M2_Progress'],
					'pValues1':pValues1,
					'sigTally1':sigTally1,
					'sim1Progress':0})
			else:
				# Record things from intro (answers to questions)

				pValues1 = [[0,0,0,0]] * 50
				sigTally1 = [[0,0,0,0]] * 50
				
				f = open('pValues1.csv', 'rU')
				mycsv = csv.reader(f)
				mycsv = list(mycsv)   

				for x in range(0,50):
					pValues1[x] = [float(mycsv[x][0]), float(mycsv[x][1]), float(mycsv[x][2]), float(mycsv[x][3])]
					sigTally1[x] = [int(mycsv[x][4]), int(mycsv[x][5]), int(mycsv[x][6]), int(mycsv[x][7])]

				self.session['pValues1'] = pValues1
				self.session['sigTally1'] = sigTally1

				doRender(self, "WithinSubjectSim1.htm",
					{'progress':self.session['M2_Progress'],
					'pValues1':pValues1,
					'sigTally1':sigTally1,
					'sim1Progress':3})

		elif M2_Progress == 2:
			# Record things from sim 1 
			self.session['WSAnswer3'] = self.request.get('Q3')
			self.session['numberOfSimulations'] = int(self.request.get('numbersims'))
			
			pValues2 = [[0,0]] * 50
			sigTally2 = [[0,0]] * 50
			correlations = [[0,0]] * 50

			f = open('pValues2.csv', 'rU')
			mycsv = csv.reader(f)
			mycsv = list(mycsv)

			for x in range(0,50):
				pValues2[x] = [float(mycsv[x][2]), float(mycsv[x][3])]
				sigTally2[x] = [int(mycsv[x][4]), int(mycsv[x][5])]
				correlations[x] = [float(mycsv[x][0]), float(mycsv[x][1])]


			doRender(self, "WithinSubjectSim2.htm",
				{'progress':self.session['M2_Progress'],
				'pValues2':pValues2,
				'sigTally2':sigTally2,
				'correlations':correlations})

		elif M2_Progress == 3:
			# Record things from sim 2
			self.session['numberOfSimulations2'] = int(self.request.get('numbersims2'))

			doRender(self, "WithinSubjectQuiz.htm",
				{'progress':self.session['M2_Progress']})

		elif M2_Progress == 4:
			# Record results of final quiz
			QuizResults = self.request.get('AnswerInput')
			QuizResults = map(str,QuizResults.split(",")) 

			self.session['QuizResults'] = QuizResults
			
			# Record that user completed the module
			self.session['Module2'] = 'Complete'
			
			# Query the datastore
			que = db.Query(User)

			# find the current user
			que = que.filter('username =', self.session['username'])
			results = que.fetch(limit=1)

			# change the datastore result for module 2
			for i in results:
				i.WSAnswer1 = self.session['WSAnswer1']
				i.WSAnswer2 = self.session['WSAnswer2']
				i.WSAnswer3 = self.session['WSAnswer3']
				i.numberOfGuesses = self.session['numberOfGuesses']
				i.numberOfSimulations = self.session['numberOfSimulations']
				i.numberOfSimulations2 = self.session['numberOfSimulations2']
				i.QuizResults = self.session['QuizResults']
				i.Module2 = self.session['Module2']
				i.put()

			logging.info('Datastore updated')

			self.session['M2_Progress'] = 0
			doRender(self, "FinishWithinSubjects.htm")
		
		elif M2_Progress < 0:
			M2_Progress += 1
			doRender(self, 'menu.htm',
				{'firstname':self.session['firstname'],
				'Module1':self.session['Module1'],
				'Module2':self.session['Module2']})

		else:
			logging.info("something is wrong")
		

class LineGraphTestHandler(webapp.RequestHandler):
	def get(self):
		# condition, x, y = readData('test',1)
		doRender(self, 'linegraph2.htm')
			# {'condition' : condition,
			# 'x' : x,
			# 'y' : y})


	# In this handler, add all the progress/back-end stuff, so that the first page rendered is the overall experiment description
	# It should then cycle through the pages to the other parts with graphs and stuff

		
###############################################################################
######################### Data Display Page Handler ###########################
###############################################################################

class DataHandler(webapp.RequestHandler):
	def get(self):

		doRender(self, 'datalogin.htm')


	def post(self):
		password=self.request.get('password')

		if password == "Bensei": # just for now


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
		
		self.session['M1_Progress'] = 0
		self.session['M2_Progress'] = 0
		self.session['M3_Progress'] = 0
		# logging.info(Logged_In)
		# If they're logged in, take them to the main menu
		if 'Logged_In' in self.session:
			if self.session['Logged_In'] == True:
				doRender(self, 'menu.htm',
					{'firstname':self.session['firstname'],
					'Module1':self.session['Module1'],
					'Module2':self.session['Module2'],
					'Module3':self.session['Module3']})

			else:
				doRender(self, 'login.htm')
		# If they aren't, take them to the login page
		else:
			self.session['Logged_In'] = False
			doRender(self, 'login.htm')

	def post(self):
		self.session = get_current_session()
		
		if int(self.request.get('guest')) == 1:
			usernum = create_or_increment_NumOfUsers()
			username = str('Guest'+str(usernum))

			logging.info('USERNAME: '+username)

			firstname = 'Guest'
			lastname = 'Guest'
			instructor = 'Guest'

			self.session = get_current_session() 
			self.session['usernum']    	= usernum
			self.session['username']   	= username
			self.session['firstname']	= firstname
			# self.session['password']    = password1
			self.session['Module1']   	= 'Incomplete'
			self.session['Module2']  	= 'Incomplete'
			self.session['Module3']  	= 'Incomplete'
			self.session['Logged_In']	= True
			self.session['M1_Progress'] = 0
			self.session['M2_Progress'] = 0
			self.session['M3_Progress'] = 0

			newuser = User(usernum=usernum, 
				username=username,
				firstname=firstname,
				lastname=self.request.get('lastname'),
				# note: this is the manual input for term. Doesn't make sense at this point to have them do this themselves since it's all for Spring 2016
				term='Spring 2016',
				
				instructor=instructor,
				# password=password1,
				Module1="Incomplete",
				Module2="Incomplete",
				Module3="Incomplete");

			newuser.put();

			doRender(self, 'menu.htm',
				{'firstname':self.session['firstname'],
				'Module1':self.session['Module1'],
				'Module2':self.session['Module2'],
				'Module3':self.session['Module3']})



			return

		username = self.request.get('username')
		# password = self.request.get('password')
		
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
		# que = que.filter('password =', password)
		# results = que.fetch(limit=1)

		# # If password mismatch
		# if len(results) == 0:
		# 	doRender(self,
		# 		'loginfailed.htm',
		# 		{'error': 'Incorrect password'})
		# 	return


		# i is a list object (basically a row of data) in the datastore. This loop saves each relevant piece of info from our query into the session.
		for i in results:
			self.session['username'] = i.username
			# self.session['password'] = i.password
			self.session['firstname'] = i.firstname
			self.session['usernum'] = i.usernum
			self.session['Module1'] = i.Module1
			self.session['Module2'] = i.Module2
			self.session['Module3'] = i.Module3
		
		self.session['M1_Progress'] = 0
		self.session['M2_Progress'] = 0
		self.session['M3_Progress'] = 0
		self.session['Logged_In'] = True


		
		doRender(self,'menu.htm',
			{'firstname':self.session['firstname'],
			'Module1':self.session['Module1'],
			'Module2':self.session['Module2'],
			'Module3':self.session['Module3']})


class LogoutHandler(webapp.RequestHandler):
	
	def get(self):	
		self.session = get_current_session()
		self.session['Logged_In'] = False	
		
		# kill all the session stuff that would identify them (username, password, etc)
		sessionlist = ['usernum', 'username', 'Module1', 'Module2', 'Module3', 'Logged_In', 'M1_Progress', 'M2_Progress', 'M3_Progress']

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
	('/CarryoverEffects', CarryoverEffectsHandler),
	('/WithinSubject', WithinSubjectHandler),
	('/PracticeFatigueEffects', PracticeFatigueEffectsHandler),
	('/LineGraphTest', LineGraphTestHandler),
	('/CarryoverEffects', CarryoverEffectsHandler),
	('/.*',  LoginHandler)],  #default page
	debug=True)

def main():
		run_wsgi_app(application)

if __name__ == '__main__':
	main()

