#!/usr/bin/env python3

"""
MAPS API
===========
This API is responsible establishing a link between the client and the database.
"""

import datetime
import json
import os
import socket
import time

import dateutil.parser
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import client, file, tools
from sqlalchemy import text
from wtforms import (Form, StringField, SubmitField, TextAreaField, TextField,
                     validators)

from Library.Errors import *
from Library.Generator import generateID
from Library.googleCalendar.CalEvents import addToCalendar, getCalendarEvents

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Define the app as an API and allow CROSS ORIGIN REQUEST SHARING (CORS).
# 	-This will allow requests to be sent from devices outside of the local network.
app = Flask(__name__)
api = Api(app)
CORS(app)

#Read in configurations.
try:
	with open('/home/pi/Assignment_Two/API/config.json', 'r') as f:
		configuration = json.load(f)

	app.secret_key = configuration['SECRET_KEY']
	API_ACCESS_KEY = configuration['API_ACCESS_KEY']

	USER   = configuration['USER']
	PASS   = configuration['PASS']
	HOST   = configuration['HOST']
	DBNAME = configuration['DBNAME']


	#Connect to database
	app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/{}'.format(USER,PASS,HOST,DBNAME)
except: print("Failed to read in configurations")

#Assign this app to both SQLAlchemy and Marshmallow.
	#	-This will allow us to execute SQL commands and Flask-Marshmallow commands.
db = SQLAlchemy(app)
ma = Marshmallow(app)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#Define dependencies to execute appointments commands
class appointments(db.Model):
    """Declaring Appointments Model"""

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_time = db.Column(db.DateTime)
    doctor_id = db.Column(db.String(10))
    patient_id = db.Column(db.String(10))
    doctor_name = db.Column(db.String(100))
    patient_name = db.Column(db.String(100))

    def __init__(self, doctor_id, patient_id, date_time, doctor_name, patient_name):
        """class constructor"""

        self.doctor_id = doctor_id
        self.patient_id = patient_id
        self.date_time = date_time
        self.doctor_name = doctor_name
        self.patient_name = patient_name

class appointmentsSchema(ma.Schema):
    """appointments schema"""

    class Meta:
       	"""Fields to expose for appointments"""

        fields = ('id', 'doctor_id', 'patient_id', 'date_time', 'doctor_name', 'patient_name')

appt_schema = appointmentsSchema()
appts_schema = appointmentsSchema(many=True)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#Define dependencies to execute doctors commands
class doctors(db.Model):
    """Declaring Doctors Model"""

    doctor_id = db.Column(db.String(10), primary_key=True, autoincrement=False, unique=True)
    title = db.Column(db.String(10))
    full_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(50))
    specialty = db.Column(db.String(100))
    regular_room = db.Column(db.Integer)

    def __init__(self, doctor_id, title, full_name, phone_number, specialty, regular_room):
        """class constructor"""

        self.doctor_id = doctor_id
        self.title = title
        self.full_name = full_name
        self.phone_number = phone_number
        self.specialty = specialty
        self.regular_room = regular_room

class doctorsSchema(ma.Schema):
    """doctors schema"""

    class Meta:
        """Fields to expose for doctors"""

        fields = ('doctor_id', 'title', 'full_name', 'phone_number', 'specialty', 'regular_room')

doctor_schema = doctorsSchema()
doctors_schema = doctorsSchema(many=True)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#Define dependencies to execute patients commands
class patients(db.Model):
    """Declaring Patients Model"""

    patient_id = db.Column(db.String(10), primary_key=True, autoincrement=False, unique=True)
    title = db.Column(db.String(10))
    full_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, patient_id, title, full_name, phone_number):
        """class constructor"""

        self.patient_id = patient_id
        self.title = title
        self.full_name = full_name
        self.phone_number = phone_number
        # self.timestamp = timestamp

class patientsSchema(ma.Schema):
    """patients schema"""

    class Meta:
        """Fields to expose for patients"""

        fields = ('patient_id', 'title', 'full_name', 'phone_number')

patient_schema = patientsSchema()
patients_schema = patientsSchema(many=True)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#Define dependencies to execute patient entries commands
class patient_db_entries(db.Model):
	"""Declaring Patient Entries Model"""

	id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
	patient_id = db.Column(db.String(10))
	entry_type = db.Column(db.String(10))
	value = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
	patient_name = db.Column(db.String(100))
	doctor_name = db.Column(db.String(100))
	doctor_id = db.Column(db.String(10))

	def __init__(self, patient_id, entry_type, value, patient_name, doctor_name, doctor_id):
		"""class constructor"""

		self.patient_id = patient_id
		self.entry_type = entry_type
		self.value = value
		self.patient_name = patient_name
		self.doctor_name = doctor_name
		self.doctor_id = doctor_id

class patient_db_entries_Schema(ma.Schema):
    """patient_db_entries schema"""

    class Meta:
        """Fields to expose for patients"""

        fields = ('id', 'patient_id', 'entry_type', 'value', 'timestamp','patient_name', 'doctor_name', 'doctor_id')

PDE_Schema = patient_db_entries_Schema()
PDEs_Schema = patient_db_entries_Schema(many=True)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class addEvent(Resource):
	"""Here users are able to add an event to the clinics google calendar.
	This function takes an Access Key, a name/title, a location, a date, a start and end time, and a description
	for the event. It returns coded messages for success (200) and failure (400)."""

	def post(self):
		"""Sending the request to add desired event"""

		#Check access key is valid
		try:	key = request.form['API_ACCESS_KEY']
		except:	return {"Code" : 400, "Message" : invalidAccessKeyError}

		if key == API_ACCESS_KEY:
			result = addToCalendar(	request.form['name'], 
									request.form['location'], 
									request.form['description'], 
									request.form['dateOnly'],
									request.form['start_time'],
									request.form['end_time'])
			return result
		else:	return {"Code" : 400, "Message" : invalidAccessKeyError}

api.add_resource(addEvent, '/addEvent')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class BookAppointment(Resource):
	"""Here users are able to make an appointment.
	This function takes an Access Key, patient id, a date and time, and a doctor name
	to complete a booking. It returns the appointments as a flask.response object."""

	def post(self):
		"""Sending the request to add booking"""

		#Check access key is valid
		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:

			#validators
			date_time_VALID, doctor_VALID, doctor_id_VALID, patient_id_VALID = False, False, False, False

			#Validate and convert date_time
			try:
				date_time = dateutil.parser.parse(request.form['date'])
				date_time_VALID = True
			except:	return dateError	

			#Validate and convert doctor and doctor ID
			try:	
				doctorName = request.form['doctor'].split('.')[1]
				doctor_VALID = True
			except:	return doctorError
			
			#Check if doctor exists, and get id.
			try:
				selectedDoctor = doctors.query.filter(doctors.full_name==doctorName).first()
				doctor_id = selectedDoctor.doctor_id
				doctor_id_VALID = True
			except:	return doctorNotExistError + " / " + doctorIdUnobtainable

			#Validate patient ID
			try:
				patient_id = request.form['pid']

				#check length of inputed id
				if len(patient_id) == 6:
					#check if patient id exists
					try:
						if patients.query.filter(patients.patient_id==patient_id).first() != None:
							data = patients.query.get(patient_id)
							patient = patient_schema.dump(data)
							patientName = patient[0]['full_name']
							patient_id_VALID = True
					except:	return incorrectPatientID
				else:	return patientLenError
			except: return patientError	

			#create new appointment entry and commit it to table in database
			if date_time_VALID == True and doctor_VALID == True and doctor_id_VALID == True and patient_id_VALID == True:

				try:	new_appt = appointments(doctor_id, patient_id, date_time, doctorName, patientName)
				except:	return apptCreateError
				try:	db.session.add(new_appt)
				except:	return apptDBaddError 
				try:	db.session.commit()
				except:	return apptCommitError 

				return appt_schema.jsonify(new_appt)
			else:	
				reply = ""
				if date_time_VALID == False: reply += "Provided date is invalid. "
				if doctor_VALID == False: reply += "Selected Doctor is invalid. "
				if doctor_id_VALID == False: reply += "Doctor ID invalid. "
				if patient_id_VALID == False: reply += "Patient ID invalid. "
				return reply
							
		else:	return invalidAccessKeyError

api.add_resource(BookAppointment, '/BookAppointment')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class GetAvailableTimes(Resource):
	"""This class obtains the events for a doctor on a particular day and increments 
	from start time to end time by given incremental factor to return a list of valid
	available times."""

	def post(self):
		"""Sending the request to get available times."""

		increment = 15
		now = datetime.datetime.now()
		date, doctor = None, None

		try: date, doctor = dateutil.parser.parse(request.form['date']), request.form['doctor']
		except: pass
		
		#If selected date is in the past return error
		if date.date() < now.date():
			return {'Code' : 400, 'Message' : pastDateSelected}

		#If selected date is today, then give remaining available times from now (can't book in the past)
		elif date.date() == now.date():

			nowTime = now.time()
			nHour = nowTime.hour
			nMinute = nowTime.minute
			nSeconds = nowTime.second
			start = (date + datetime.timedelta(hours=nHour, minutes=nMinute, seconds=nSeconds))
			end = (date + datetime.timedelta(hours=23, minutes=59, seconds=59))

		#if selected date is > todays.date(), start from 0H:0M:0S, to show all availabilities for that day.
		else:
			start = date
			end = (date + datetime.timedelta(hours=23, minutes=59, seconds=59))

		try:	return getCalendarEvents(doctor, start, end, increment)
		except:	return {'Code' : 400, 'Message' : calenarGetEventsError}

api.add_resource(GetAvailableTimes, '/GetAvailableTimes')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class GetNewPatientID(Resource):
	"""This function generates a new patient id for patients when registering.
	It takes an Access Key and returns a new 6 character long id that does not exist 
	currently in the system. The generator used supports upto 2,176,782,336 ID's"""

	def post(self):
		"""Sending the request to get available times."""

		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:
			try:
				id = generateID()
				while patients.query.filter(patients.patient_id==id).first() != None:
					id = generateID()
				return id
			except Exception as e:
				return "exception: " + str(e)

		else:	return invalidAccessKeyError

api.add_resource(GetNewPatientID, '/GetNewPatientID')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class AddPatient(Resource):	
	"""This function allows for adding a new patient to the database.
	It takes an Access Key, a patient id, a patient title, a patient full name, and phone number
	to complete the registration.

	This function can be modified to accept more uniquely identifiable patient data such as medicare number,
	social security number, etc.
	It returns nothing on succession, and error messages on failure."""

	def post(self):
		"""Sending add patient request"""

		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:
			try:
				data = patients.query.filter(patients.full_name==request.form['patientFN']).first()

				#A patient already exists with the same name, 
				#check phone number to confirm if they are the same person
				#this feature can be modified to check a medicare number or
				#a more unique identifier in general.
				if data:
					patient = patient_schema.dump(data)
					if patient[0]['phone_number'] == request.form['phone_number']:
						return alreadyRegistered

				try:
					new_patient = patients(request.form['patientID'], request.form['patientTitle'], 
									request.form['patientFN'], request.form['phone_number'])
					db.session.add(new_patient)
					db.session.commit()
					return
				except:	return errorCommitingDb
			except:	return blankField
		else:
			return invalidAccessKeyError

api.add_resource(AddPatient, '/AddPatient')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class GetPatientRecords(Resource):	
	"""This function takes an Access Key and a patient id, 
	and returns a flask.response object with all the appointments associated to that patient id."""

	def post(self):
		"""Get data from database"""

		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:
			if request.form['pid'] and request.form['pid'] != "":
				pid = request.form['pid']
				try:
					patientRecords = patient_db_entries.query.filter(patient_db_entries.patient_id==pid).all()
					return PDEs_Schema.jsonify(patientRecords)
				except:	return invalidDbRequest + "\n" + str(patient_db_entries.query.filter(patient_db_entries.patient_id==pid).all())
			else:	return patientRecordsGetError
		else:	return invalidAccessKeyError

api.add_resource(GetPatientRecords, '/GetPatientRecords')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class GetPatient(Resource):
	"""This function takes an Access Key and patient id, 
	and returns a flask.response patient object associated to the patient id."""	

	def post(self):
		"""Get data from database"""

		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:
			if request.form['pid'] and request.form['pid'] != "":
				pid = request.form['pid']
				try:
					patient = patients.query.get(pid)
					return patient_schema.jsonify(patient)
				except:	return invalidDbRequest
			else:	return patientRecordsGetError
		else:	return invalidAccessKeyError

api.add_resource(GetPatient, '/GetPatient')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class AddPatientRecord(Resource):	
	"""This function allows for adding a medical record for a patient. It supports 2 types of entries, Notes and Diagnosis.
	It takes an Access Key, a patient id, an entry type, an entry value, a patient name, a doctor name (the doctor making the entry), 
	and that doctors id.
	It returns nothing on succession, and error messages on failure."""

	def post(self):
		"""Send data to add"""

		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:
			if ((request.form['patient_id'] and request.form['patient_id'] != "") and
			(request.form['entry_type'] and request.form['entry_type'] != "") and
			(request.form['value'] and request.form['value'] != "") and
			(request.form['patient_name'] and request.form['patient_name'] != "") and
			(request.form['doctor_name'] and request.form['doctor_name'] != "") and
			(request.form['doctor_id'] and request.form['doctor_id'] != "")):
				try:
					new_patientEntry = patient_db_entries(request.form['patient_id'], request.form['entry_type'], request.form['value'], 
					request.form['patient_name'], request.form['doctor_name'], request.form['doctor_id'])
					db.session.add(new_patientEntry)
					db.session.commit()
					return
				except:	return generalError1
			else:	return blankField
		else:	return invalidAccessKeyError

api.add_resource(AddPatientRecord, '/AddPatientRecord')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class GetPatientAppointments(Resource):	
	"""This function takes an Access Key and patient id, 
	to return a flask.response object of all the associated appointments with that id."""

	def post(self):
		"""Get data from database"""

		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:
			if request.form['pid'] and request.form['pid'] != "":
				pid = request.form['pid']
				try:
					patientAppts = appointments.query.filter(appointments.patient_id==pid).all()
					return appts_schema.jsonify(patientAppts)
				except:	return invalidDbRequest
			else:	return getApptsError
		else:	return invalidAccessKeyError

api.add_resource(GetPatientAppointments, '/GetPatientAppointments')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class GetAllAppointments(Resource):
	"""This function takes an Access Key and patient id, 
	to return a flask.response object of all the associated appointments with that id."""	

	def post(self):
		"""Get data from database"""

		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:
			try:	docName = request.form['doctorName'].split(".")[1].strip()
			except:	return doctorMissing
			try:
				sql = text('SELECT * FROM appointments WHERE date_time >= ' + "'" + request.form['apptsFrom']+ "'" + 
				' AND date_time <= ' + "'" + request.form['apptsTo'] + "'" +' AND doctor_name = ' + "'" + docName + "'")
				result = db.engine.execute(sql)
				return appts_schema.jsonify(result)
			except:	return invalidDbRequest
		else:	return invalidAccessKeyError

api.add_resource(GetAllAppointments, '/GetAllAppointments')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class DeletePatientAppointment(Resource):	
	"""This function allows for deleting a patient appointment.
	it takes an Access Key, and an appointment id. It then returns a
	flask.response object of the deleted item."""

	def post(self):
		"""Send delete request to database"""

		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:
			if request.form['apptID'] and request.form['apptID'] != "":
				apptID = request.form['apptID']
				try:
					patientAppt = appointments.query.get(apptID)
					db.session.delete(patientAppt)
					db.session.commit()
					return appt_schema.jsonify(patientAppt)
				except:	return invalidDbRequest
			else:	return deleteApptERROR
		else:	return invalidAccessKeyError

api.add_resource(DeletePatientAppointment, '/DeletePatientAppointment')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class GetPatientsSeen(Resource):	
	"""This function takes an Access key, a doctor title and name, 
	a start date and end date (for which you wish to search within), and returns 
	a flask.response object of all the appointments for that doctor."""

	def post(self):
		"""Get data from database"""

		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:
			if ((request.form['doctor'] and request.form['doctor'] != "") and
			(request.form['startDate'] and request.form['startDate'] != "") and
			(request.form['endDate'] and request.form['endDate'] != "")):
				try:
					selectedDoctorFullName = request.form['doctor'].split(".")[1]
					sql = text('SELECT * FROM appointments WHERE date_time >= ' + "'" + request.form['startDate']+ "'" + 
					' AND date_time <= ' + "'" +request.form['endDate']+ "'" + ' AND doctor_name= ' + "'" +selectedDoctorFullName +"'")
					result = db.engine.execute(sql)
					return appts_schema.jsonify(result)
				except:	return invalidDbRequest
			else:
				errorDict = [{"ERROR MESSAGE: " : "The following errors occured:"}]

				for i in [None, ""]: errorDict.append({"doctor ID Error" : "Doctor ID is blank."}) if request.form['doctor'] == i else None
				for i in [None, ""]: errorDict.append({"Start Date Error" : "Start Date is blank."}) if request.form['startDate'] == i else None
				for i in [None, ""]: errorDict.append({"End Date Error" : "End Date is blank."}) if request.form['endDate'] == i else None

				return jsonify(errorDict)
		else:	return invalidAccessKeyError

api.add_resource(GetPatientsSeen, '/GetPatientsSeen')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class GetDoctors(Resource):	
	"""This function takes an Access Key and returns all doctors on record."""

	def post(self):
		"""Get data from database"""

		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:
			try:
				allDoctors = doctors.query.all()
				result = doctors_schema.dump(allDoctors)
				return doctors_schema.jsonify(result.data)
			except:	return invalidDbRequest
		else:	return invalidAccessKeyError

api.add_resource(GetDoctors, '/GetDoctors')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class DeleteDoctor(Resource):	
	"""This function take an Access Key and a doctor name, and returns confirmation of result as a string."""

	def post(self):
		"""Send delete request to database"""

		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:
			if request.form['doctorName'] and request.form['doctorName'] != "":
				try:
					doctorName = request.form['doctorName']
					dbData = doctors.query.filter(doctors.full_name==doctorName).all()
					result = doctors_schema.dump(dbData)
					data = result[0]
				except:	return invalidDbRequest

				if(len(data) > 1):	return duplicateDoctors
				elif(len(data) == 0):	return doctorNotFound
				else:
					try:
						doctorRm = doctors.query.get(data[0]['doctor_id'])
						db.session.delete(doctorRm)
						db.session.commit()
						replyStr = str(data[0]['title']) + "." + str(data[0]['full_name']) + " has been successfully removed from the database."
						return replyStr
					except:	return invalidDbRequest
			else:	return blankField
		else:	return invalidAccessKeyError

api.add_resource(DeleteDoctor, '/DeleteDoctor')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class AddDoctor(Resource):	
	"""This function take an Access Key, a doctor id, a title, a doctor full name, a phone number, a specialty and a regular room
	to create a new doctor record in the system. It returns a string of confirmation of result."""

	def post(self):
		"""Send data to add to database"""

		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:

			if ((request.form['doctor_id'] and request.form['doctor_id'] != "") and
			(request.form['title'] and request.form['title'] != "") and
			(request.form['full_name'] and request.form['full_name'] != "") and
			(request.form['phone_number'] and request.form['phone_number'] != "") and
			(request.form['specialty'] and request.form['specialty'] != "") and
			(request.form['regular_room'] and request.form['regular_room'] != "")):
				try:
					new_doctor = doctors(request.form['doctor_id'], request.form['title'], request.form['full_name'], 
					request.form['phone_number'], request.form['specialty'], request.form['regular_room'])
					db.session.add(new_doctor)
					db.session.commit()
					replyStr = (str(request.form['title']) + "." + str(request.form['full_name']) + 
								" has been successfully added to the database. [ID: " + str(request.form['doctor_id']) + "]")
					return replyStr
				except:	return generalError1
			else:	return blankField
		else:	return invalidAccessKeyError

api.add_resource(AddDoctor, '/AddDoctor')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#Run Program
if __name__ == '__main__':
	try:
		ip_address = os.popen('hostname -I').read().split(" ")
		app.run(host = ip_address[0], port=5001, debug=True)
	except Exception:
		print("Error executing app.run with hostname -I")
		try:
			ip_address = socket.gethostname()
			app.run(host = ip_address, port=5001, debug=True)
		except Exception:
			print("Error aqcuiring host ip address via socket and executing app.run")
			try:
				ip_address = os.popen('hostname -i').read()
				app.run(host = ip_address, port=5001, debug=True)
			except Exception:
				print("Could not run app.run at all!")
