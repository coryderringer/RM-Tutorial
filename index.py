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
	account = 			db.StringProperty()
	usernum =			db.IntegerProperty()
	created =			db.DateTimeProperty(auto_now=True)
	datalist =			db.ListProperty(int)
	Completion_Code = 	db.IntegerProperty()
	sex =				db.IntegerProperty()
	ethnicity =			db.IntegerProperty()
	race =				db.IntegerProperty()	
	BonusList =			db.ListProperty(int)
	condition =			db.IntegerProperty()

class ScenarioData(db.Model):
	user  =				db.ReferenceProperty(User)
	usernum =			db.IntegerProperty()
	account =			db.StringProperty()
	created =			db.DateTimeProperty(auto_now=True)
	scenario =			db.IntegerProperty()
	dataset =			db.IntegerProperty()
	DrugArray =			db.ListProperty(int)
	DrugIDs = 			db.ListProperty(int)
	FinalJudgments = 	db.ListProperty(int)
	TJs =				db.ListProperty(int)
	Bonus =				db.IntegerProperty()
	drugphotos =		db.ListProperty(int)

	
class PracticeData(db.Model):
	usernum =			db.IntegerProperty()
	PJs =				db.ListProperty(int)
	PracticeArray =		db.ListProperty(int)
	

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
		self.session = get_current_session()
		scenario = self.session['scenario']
		datalist = self.session['datalist']
		PatientNames = self.session['PatientNames']
		photolist = self.session['photolist']
		
		#identify the photos participants will see
		drugphotos = photolist[scenario]
		self.session['drugphotos'] = drugphotos
		logging.info(drugphotos)


		CurrentPatient = PatientNames[scenario]

		#identify current dataset
		n = datalist[scenario]
		
		#placeholder data, 6th row is order within the dataset (1-14)
		CurrentData = [[0,0,0,0,0,0]] * 14

		# Open the csv file, read in the appropriate data for this scenario
		f = open('data.csv', 'rU')
		mycsv = csv.reader(f)
		mycsv = list(mycsv)   

		for x in range(0,14):
			CurrentData[x] = [int(mycsv[((n-1)*14)+x][0]), int(mycsv[((n-1)*14)+x][1]), int(mycsv[((n-1)*14)+x][2]), int(mycsv[((n-1)*14)+x][3]), int(mycsv[((n-1)*14)+x][4]), int(mycsv[((n-1)*14)+x][5])]

		# Data goes into JS unscrambled. All of the randomizations are done in JS, which makes it easier to keep track.
		# condition = self.session['condition']
		
		# for testing
		condition = 0

		doRender(
			self, 'scenario.htm',
			{'scenario':scenario,
			'CurrentData':CurrentData,
			'n':n,
			'LengthOfData':LengthOfData,
			'condition':condition,
			'CurrentPatient':CurrentPatient,
			'drugphotos':drugphotos})
				#get rid of spy photos
	

	def post(self):

		self.session = get_current_session()
		scenario = self.session['scenario']
		datalist = self.session['datalist']
		PatientNames = self.session['PatientNames']
		BonusList = self.session['BonusList']
		n = datalist[scenario]


		TJs = self.request.get('TJInput')
		TJs = map(int,TJs.split(",")) 


		Bonus = self.request.get('BonusInput')
		Bonus = map(int,Bonus.split(","))
		Bonus = sum(Bonus)

		#update bonuslist
		BonusList.append(Bonus)
		self.session['BonusList'] = BonusList

		DrugArray = self.request.get('DrugArrayInput')
		DrugArray = map(int,DrugArray.split(","))

		DrugIDs = self.request.get('DrugIDs')
		DrugIDs = map(int,DrugIDs.split(","))

		FinalJudgments = DrugArray[(len(DrugArray)-4):len(DrugArray)]

		
		#This is how we send collected data to datastore
		newinput = ScenarioData(user=self.session['userkey'],
			usernum=self.session['usernum'],
			account=self.session['username'],
			scenario=scenario,
			dataset=n, 
			DrugArray=DrugArray,
			FinalJudgments=FinalJudgments,
			Bonus=Bonus,
			TJs=TJs,
			drugphotos=self.session['drugphotos'],
			DrugIDs=DrugIDs);

		newinput.put();


		logging.info(Bonus)
		self.session['scenario']+=1
		scenario=self.session['scenario']
		

		if scenario<=NumScenarios-1: #have more scenarios to go
			CurrentPatient = PatientNames[scenario]
			doRender(self, 'newscenario.htm',
				{'scenario':scenario,
				'CurrentPatient':CurrentPatient})
		
		else: 
			doRender(self, 'demographics.htm')



################################################################################
############################## Small Handlers ##################################
################################################################################


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

		if password == "gZ2BYJxfCY5SiyttS8zl":

			que=db.Query(ScenarioData)
			que.order("usernum").order("scenario")
			
			d=que.fetch(limit=10000)
				


			que2=db.Query(User)
			que2.order("usernum")
			u=que2.fetch(limit=10000)
			
			que3=db.Query(PracticeData)
			que3.order("usernum")
			p=que3.fetch(limit=10000)

			doRender(
				self, 
				'data.htm',
				{'u':u,
				'd':d,
				'p':p,
				'LengthOfData':LengthOfData,
				'NumScenarios':NumScenarios})
		else:
			doRender(self, 'dataloginfail.htm')


class QualifyHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, 'qualify.htm')
		
class DNQHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, 'do_not_qualify.htm')    

################################################################################
############################ DemographicsHandler ###############################
################################################################################
# This handler is a bit confusing - it has all this code to calculate the
# correct race number

class DemographicsHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, 'demographics.htm')
		
	def post(self):
		self.session=get_current_session()
		
		sex=int(self.request.get('sex'))
		ethnicity=int(self.request.get('ethnicity'))
		racel=map(int,self.request.get_all('race')) #race list
		logging.info("race list")   
		logging.info(racel)

		rl1=int(1 in racel)
		rl2=int(2 in racel)
		rl3=int(3 in racel)
		rl4=int(4 in racel)
		rl5=int(5 in racel)
		rl6=int(6 in racel)
		rl7=int(7 in racel)
		
#Amer Indian, Asian, Native Hawaiian, Black, White, More than one, No Report
#race_num is a number corresponding to a single race AmerInd (1) - White(5)
		race_num=rl1*1+rl2*2+rl3*3+rl4*4+rl5*5
		
		morethanonerace=0
		for i in [rl1,rl2,rl3,rl4,rl5]:
				if i==1:
						morethanonerace+=1
		if rl6==1:
				morethanonerace+=2
				
		if rl7==1:  #dont want to report
				race=7
		elif morethanonerace>1:
				race=6
		elif morethanonerace==1:
				race=race_num
		
		logging.info("race")
		logging.info(race)
		
		
		
		Completion_Code=random.randint(10000000,99999999)
		
		
		obj = User.get(self.session['userkey']);
		obj.Completion_Code = Completion_Code
		obj.BonusList = self.session['BonusList']
		obj.sex = sex
		obj.ethnicity = ethnicity
		obj.race = race
		obj.put();
		
		
		self.session.__delitem__('usernum')
		self.session.__delitem__('username')
		self.session.__delitem__('userkey')
		self.session.__delitem__('scenario')
		self.session.__delitem__('BonusList')
		self.session.__delitem__('datalist')

		doRender(self, 'logout.htm', {'Completion_Code': Completion_Code, })
		

################################################################################
############################### MturkIDHandler #################################
################################################################################
	  
class MturkIDHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, 'mturkid.htm')

	def post(self):
		ID=self.request.get('ID')
		acct=ID ##no reason

		form_fields = {
			"ID": ID,
			"ClassOfStudies": 'Cory Experiment 3',
			"StudyNumber": 1
			}

		form_data = urllib.urlencode(form_fields)
		url="http://www.mturk-qualify.appspot.com"
		result = urlfetch.fetch(url=url,
								payload=form_data,
								method=urlfetch.POST,
								headers={'Content-Type': 'application/x-www-form-urlencoded'})

		if result.content=="0":
			#self.response.out.write("ID is in global database.")
			doRender(self, 'do_not_qualify.htm')
		
		elif result.content=="1":
			# Check if the user already exists
			que = db.Query(User).filter('account =',ID)
			results = que.fetch(limit=1)
		
			logging.info('test')

			# Allows username 'ben' to pass. You can't just allow other names to pass - it needs to be changed in http://www.mturk-qualify.appspot.com too
			if (len(results) > 0) & (ID!='ben'):   
				doRender(self, 'do_not_qualify.htm')

			# If user is qualified (http://www.mturk-qualify.appspot.com returns 1)
			else:
				#Create the User object and log the user in.
				usernum = create_or_increment_NumOfUsers()

				#Make the data that this subject will see.
				#It is made once and stored both in self.session and in database				

				datalistLO = random.sample(xrange(1,21), 2)
				datalistHI = random.sample(xrange(21,41), 2)
				datalist = [datalistLO[0], datalistLO[1], datalistHI[0], datalistHI[1]]
				random.shuffle(datalist)

				# create a randomly ordered list from 0-15 (Python is weird...yes you use xrange(0,16) even though it only goes to 15).
				photolist = random.sample(xrange(0,4),4)


				PatientNames = ['Robert S.', 'James W.', 'Mary G.', 'Betty J.']
				random.shuffle(PatientNames)

				randomizations = [0,1]
				condition = random.choice(randomizations)

				newuser = User(account=acct, usernum=usernum, condition=condition, datalist=datalist);

				# dataframe modeling, but I'm not sure what exactly
				userkey = newuser.put()
				# this stores the new user in the datastore
				newuser.put()

				# store these variables in the session
				self.session=get_current_session() #initialize sessions
				self.session['usernum']		= usernum
				self.session['username']	= acct
				self.session['userkey']		= userkey
				self.session['scenario']	= 0
				self.session['BonusList']	= []
				self.session['practice']	= 0
				self.session['condition'] = condition
				self.session['PatientNames'] = PatientNames
				self.session['datalist']	= datalist
				self.session['photolist'] = photolist
				doRender(self, 'qualify.htm')


		# If got no response back from http://www.mturk-qualify.appspot.com
		else:
		  error="The server is going slowly. Please reload and try again."
		  self.response.out.write(result.content)

		
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
	('/demographics', DemographicsHandler),
	('/mturkid', MturkIDHandler), 
	('/.*',      MturkIDHandler)],  #default page
	debug=True)

def main():
		run_wsgi_app(application)

if __name__ == '__main__':
	main()

