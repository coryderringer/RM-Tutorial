import os, logging, wsgiref.handlers, datetime, random, math, string, urllib, csv

from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template 
from gaesessions import get_current_session
from google.appengine.api import urlfetch



LengthOfData=14    
NumScenarios=4





################################################################################
################################################################################
######################## Data Classes for Database #############################
################################################################################
################################################################################

class User(db.Model):
	username = 			db.StringProperty()
	usernum = 			db.IntegerProperty()
	password =			db.StringProperty()
	created =			db.StringProperty()
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



################################################################################
################################################################################
########################### From Book Don't Touch ##############################
################################################################################
################################################################################
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
###################### Handlers for Individual Pages ###########################
################################################################################
################################################################################

################################################################################
############################## ScenarioHandler #################################
################################################################################
# The main handler for all the "scenarios" (e.g., one patient)
class ScenarioHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, 'scenario.htm')
	

	def post(self):
		doRender(self, 'scenario.htm')



################################################################################
############################## Small Handlers ##################################
################################################################################

class SignupHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, 'signup.htm')

	def post(self):
		self.session = get_current_session()
		username = self.request.get('username')
		password1 = self.request.get('password1')
		password2 = self.request.get('password2')

		if password1 != password2:
			doRender(self, 'error.htm')
		else:
			usernum = create_or_increment_NumOfUsers()
			newuser = User(usernum=usernum, 
				username=username,
				password=password1,
				Module1="Incomplete",
				Module2="Incomplete");


			# dataframe modeling, but I'm not sure what exactly
			userkey = newuser.put()
			# this stores the new user in the datastore
			newuser.put()

			# store these variables in the session
			self.session=get_current_session() #initialize sessions
			self.session['usernum']    	= usernum
			self.session['username']   	= username
			self.session['password']    = password1
			self.session['Module1']   	= 'Incomplete'
			self.session['Module2']  	= 'Incomplete'


			doRender(self, 'congratulations.htm')




			

			# #This is how we send user's data to datastore
			# newuser = User(usernum=usernum,
	  #           username=self.request.get('username'),
	  #           password=password1,
	  #           Module1='Incomplete',
	  #           Module2='Incomplete');

   #          # dataframe modeling, but I'm not sure what exactly
	  #       userkey = newuser.put()
	  #       # this stores the new user in the datastore
	  #       newuser.put()

			# doRender(self, 'congratulations.htm') # for now
		



class InstructionsHandler(webapp.RequestHandler):
	def get(self):
		self.session = get_current_session()
		self.session['practice'] = 0
		doRender(self, 'instructions.htm')


class PracticeHandler(webapp.RequestHandler):
	def get(self):
		self.session = get_current_session()
		
		
		self.session['practice'] += 1

		if self.session['practice'] == 1:
			practice = self.session['practice']
			doRender(self, 'practice.htm',
			{'practice':practice})
		else:
			# Make the data for the practice session:

			#placeholder data, 6th row is order within the dataset (1-14)
			CurrentData = [[0,0,0,0,0]] * 14

			# Open the csv file, read in the appropriate data for this scenario
			f = open('practicedata.csv', 'rU')
			mycsv = csv.reader(f)
			mycsv = list(mycsv)   

			for x in range(0,7):
				CurrentData[x] = [int(mycsv[x][0]), int(mycsv[x][1]), int(mycsv[x][2]), int(mycsv[x][3]), int(mycsv[x][4])]



			doRender(self, 'practice2.htm',
					{'CurrentData':CurrentData})

	def post(self):

		self.session=get_current_session()
		PJs = self.request.get('PJInput')
		PJs = map(int, PJs.split(","))

		PracticeArray = self.request.get('PracticeArrayInput')
		PracticeArray = map(int, PracticeArray.split(","))

		newinput = PracticeData(user=self.session['userkey'],
			usernum=self.session['usernum'],
			PJs = PJs,
			PracticeArray = PracticeArray);

		logging.info(PracticeArray)

		newinput.put();

		doRender(self,'bonus.htm')


class DataHandler(webapp.RequestHandler):
	def get(self):

		doRender(self, 'datalogin.htm')


	def post(self):
		password=self.request.get('password')

		if password == " ": # just for now


			que2=db.Query(User)
			que2.order("usernum")
			users=que2.fetch(limit=10000)

			doRender(
				self, 
				'data.htm',
				{'users':users})
		else:
			doRender(self, 'dataloginfail.htm')


class QualifyHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, 'qualify.htm')
		
class DNQHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, 'do_not_qualify.htm')    

################################################################################
############################### LogoutHandler ##################################
################################################################################
# This handler is a bit confusing - it has all this code to calculate the
# correct race number

class LogoutHandler(webapp.RequestHandler):
	def post(self):		
		# kill all the session stuff that would identify them (username, password, etc)
		self.session.__delitem__('usernum')
		self.session.__delitem__('username')
		self.session.__delitem__('userkey')
		self.session.__delitem__('scenario')
		self.session.__delitem__('BonusList')
		self.session.__delitem__('datalist')

		# Send them back to the login page
		doRender(self, 'login.htm')


		

################################################################################
############################### LoginHandler ###################################
################################################################################
	  
class LoginHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, 'login.htm')

	def post(self):
		username = self.request.get('ID')


		que2=db.Query(User)
		que2.order("usernum")
		users=que2.fetch(limit=10000)

		print users[0]

		doRender(self, 'congratulations.htm')



		# password_input = self.request.get('password')

		# # Pull username and password from user database.
		# password = "password" # just for now
		# exists = True # just for now

		# # check if account exists

		# if exists == False:
		# 	doRender(self, 'no_account.htm')
		# else:
		# 	if password_input != password:
		# 		doRender(self, 'loginfailed.htm')
		# 	else:
		# 		if username == 'admin': 	# Pull data from the user database
		# 			doRender(self, 'adminview.htm')
		# 		else:
		# 			doRender(self,'congratulations.htm')



		
################################################################################
############################### MainAppLoop ####################################
################################################################################ 

application = webapp.WSGIApplication([
	('/instructions', InstructionsHandler),
	('/practice', PracticeHandler),
	('/data', DataHandler),
	('/do_not_qualify', DNQHandler),
	('/scenario', ScenarioHandler),
	('/qualify', QualifyHandler),
	('/logout', LogoutHandler),
	('/login', LoginHandler),
	('/signup', SignupHandler),
	('/.*',  LoginHandler)],  #default page
	debug=True)

def main():
		run_wsgi_app(application)

if __name__ == '__main__':
	main()

