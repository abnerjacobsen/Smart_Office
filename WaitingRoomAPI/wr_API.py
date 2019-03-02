#!/usr/bin/env python3

"""
MAPS API
===========
This API is responsible managing the waiting room list.
It allows for :
	-patients to be put on the list on arrival.
	-doctor to get next patient.
	-calling in next patient.
	-doctor to clear seen patients from waiting list.
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

import aiy.audio
from Library.Errors import *

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Define the app as an API and allow CROSS ORIGIN REQUEST SHARING (CORS).
# 	-This will allow requests to be sent from devices outside of the local network.
app = Flask(__name__)
api = Api(app)
CORS(app)

#Read in configurations.
try:
	with open('/home/pi/Assignment_Two/WaitingRoomAPI/config.json', 'r') as f:
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
#Define dependencies to execute waiting room commands
class waiting_room(db.Model):
    """Declaring Waiting Room Model"""

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_time = db.Column(db.DateTime)
    doctor_id = db.Column(db.String(10))
    patient_id = db.Column(db.String(10))
    doctor_name = db.Column(db.String(100))
    patient_name = db.Column(db.String(100))
    arrival_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, doctor_id, patient_id, date_time, doctor_name, patient_name):
        """class constructor"""

        self.doctor_id = doctor_id
        self.patient_id = patient_id
        self.date_time = date_time
        self.doctor_name = doctor_name
        self.patient_name = patient_name

class waiting_room_schema(ma.Schema):
    """waiting room schema"""

    class Meta:
       	"""Fields to expose for waiting room"""

        fields = ('id', 'doctor_id', 'patient_id', 'date_time', 'doctor_name', 'patient_name', 'arrival_time')

wRoom_schema = waiting_room_schema()
wRooms_schema = waiting_room_schema(many=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class callPatientIn(Resource):
	"""Here a patient is called in to see the calling doctor."""

	def post(self):
		"""Make call-in announcement."""
	
		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:
			if ((request.form['patientName'] and request.form['patientName'] != "") and
				(request.form['doctor'] and request.form['doctor'] != "")):
				try:
					aiy.audio.say(request.form['patientName'] + ", Doctor " + request.form['doctor'] + " will see you now. Please come in.")
					return {'code' : 200, 'message' : "Patient has been called in."}
				except:	return {'code' : 400, 'message' : "AIY ERROR"}
			else: return {'code' : 400, 'message' : "Invalid Request, could not make announcement."}
		else:	return {'code' : 400, 'message' : invalidAccessKeyError}

api.add_resource(callPatientIn, '/callPatientIn')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class addToWaitingRoom(Resource):
	"""Here  Google Assistant will add the newly arrived persons appointment to the waiting room list."""

	def post(self):
		"""Sending the request to add waiting patient appointment"""

		fieldsGood = False
		#Check access key is valid
		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:

			try:
				date_time = request.form['date_time']
				doctor_id = request.form['doctor_id']
				patient_id = request.form['patient_id']
				doctor_name = request.form['doctor_name']
				patient_name = request.form['patient_name']
				fieldsGood = True
			except: return {'code' : 400, 'message' : "invalid field"}

			#create new appointment entry and commit it to table in database
			if fieldsGood == True:

				try:	
					new_waiting = waiting_room(doctor_id, patient_id, date_time, doctor_name, patient_name)
					db.session.add(new_waiting)
					db.session.commit()
				except Exception as e:	return {'code' : 400, 'message' : "Database Error: " + str(e)}

				return {'code' : 200, 'message' : "Added to waiting room"}							
		else:	return {'code' : 400, 'message' : invalidAccessKeyError}

api.add_resource(addToWaitingRoom, '/addToWaitingRoom')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class getNextAppointment(Resource):
	"""Here the next appointment ("patient") will be found and returned to querying party
	from the waiting room database."""

	def post(self):
		"""Sending the request to retrieve next waiting patient appointment"""

		fieldsGood = False
		#Check access key is valid
		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:

			try:
				if request.form['doctor_id'] and request.form['doctor_id'] != "":
					doctor_id = request.form['doctor_id']
					fieldsGood = True
			except: return {'code' : 400, 'message' : "invalid field"}
			
			#get next appointment
			if fieldsGood == True:

				try:	
					sql = text('SELECT * FROM (SELECT * FROM waiting_room WHERE doctor_id = ' + 
					"'" + doctor_id + "'" + ') as a WHERE date_time = (SELECT MIN(date_time) FROM \
					(SELECT * FROM waiting_room WHERE doctor_id = ' + "'" + doctor_id + "'" + ') as b)')
			
					result = db.engine.execute(sql)
					return wRooms_schema.jsonify(result)

				except Exception as e:	return {'code' : 400, 'message' : "Database Error: " + str(e)}

				return {'code' : 200, 'message' : "Added to waiting room"}							
		else:	return {'code' : 400, 'message' : invalidAccessKeyError}

api.add_resource(getNextAppointment, '/getNextAppointment')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class appointmentComplete(Resource):
	"""Here the completed appointment will be removed from the waiting room"""

	def post(self):
		"""Sending the request to remove waiting patient appointment"""

		fieldsGood = False
		#Check access key is valid
		try:	key = request.form['API_ACCESS_KEY']
		except:	return accessKeyMissing

		if key == API_ACCESS_KEY:

			try:
				if request.form['appt_id'] and request.form['appt_id'] != "":
					apptID = request.form['appt_id']
					fieldsGood = True
			except: return {'code' : 400, 'message' : "invalid field"}
			
			#delete the what was once 'next' appointment
			if fieldsGood == True:
				try:	
					patientAppt = waiting_room.query.get(apptID)
					db.session.delete(patientAppt)
					db.session.commit()
					return {'code' : 200, 'message' : "Removed from waiting room."}
				except Exception as e:	return {'code' : 400, 'message' : "Database Error: " + str(e)}
		else:	return {'code' : 400, 'message' : invalidAccessKeyError}

api.add_resource(appointmentComplete, '/appointmentComplete')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Run Program
if __name__ == '__main__':
	try:
		ip_address = os.popen('hostname -I').read().split(" ")
		app.run(host = ip_address[0], port=5006, debug=True)
	except Exception:
		print("Error executing app.run with hostname -I")
		try:
			ip_address = socket.gethostname()
			app.run(host = ip_address, port=5006, debug=True)
		except Exception:
			print("Error aqcuiring host ip address via socket and executing app.run")
			try:
				ip_address = os.popen('hostname -i').read()
				app.run(host = ip_address, port=5006, debug=True)
			except Exception:
				print("Could not run app.run at all!")
