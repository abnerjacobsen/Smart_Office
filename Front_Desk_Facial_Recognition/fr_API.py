#!/usr/bin/env python3

"""
Front Reception Facial Recognition API
===========
This API is responsible identifying a patient via facial recognition.
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
from recognition.recognise import recognise

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Define the app as an API and allow CROSS ORIGIN REQUEST SHARING (CORS).
# 	-This will allow requests to be sent from devices outside of the local network.
app = Flask(__name__)
api = Api(app)
CORS(app)

#Read in configurations.
try:
	with open('/home/pi/Assignment_Two/Front_Desk_Facial_Recognition/config.json', 'r') as f:
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
class recognisePatient(Resource):
	"""Here, via RPC the patient is recognised using the webcam"""

	def post(self):
		"""returning a matched persons data"""

		#Check access key is valid
		try:	key = request.form['API_ACCESS_KEY']
		except:	return {"code" : 400, "message" : invalidAccessKeyError}

		if key == API_ACCESS_KEY:
			try:
				patientIdentified = recognise()
				if patientIdentified['code'] == 200:
					name = patientIdentified['identified'].split("-")[0].strip().replace("_", " ")
					id = patientIdentified['identified'].split("-")[1].strip()

					patientAppts = appointments.query.filter(appointments.patient_id==id).all()
					data = appts_schema.dump(patientAppts)[0]
				
					todaysDate = datetime.datetime.now().date()
					apptsForToday = []
					for appt in data:
						if dateutil.parser.parse(appt['date_time']).date() == todaysDate:
							apptsForToday.append(appt)
					
					return jsonify(apptsForToday)
			except: return {'code' : 400}

			else: return {'code' : 400}

		else:	return {"Code" : 400, "Message" : invalidAccessKeyError}

api.add_resource(recognisePatient, '/recognisePatient')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Run Program
if __name__ == '__main__':
	try:
		ip_address = os.popen('hostname -I').read().split(" ")
		app.run(host = ip_address[0], port=5005, debug=True)
	except Exception:
		print("Error executing app.run with hostname -I")
		try:
			ip_address = socket.gethostname()
			app.run(host = ip_address, port=5005, debug=True)
		except Exception:
			print("Error aqcuiring host ip address via socket and executing app.run")
			try:
				ip_address = os.popen('hostname -i').read()
				app.run(host = ip_address, port=5005, debug=True)
			except Exception:
				print("Could not run app.run at all!")
