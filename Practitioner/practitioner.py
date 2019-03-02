#!/usr/bin/env python3

"""This is the practitioners webservice, which enables practitioners to upload notes and diagnosises
for a patient, and also view their records. Additionally practitioners can state their availability for
a single day, or a range of days."""

import datetime
import json
import os
import random
import socket
import sqlite3
import time
import urllib.request
from functools import wraps
from flask_cors import CORS

import dateutil.parser
import pygal
import requests
from flask import Flask, flash, render_template, request
from wtforms import (Form, StringField, SubmitField, TextAreaField, TextField,
                     validators)

from Forms.Forms import DVPForm1, DVPForm2, SAForm

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

app = Flask(__name__)
app.config.from_object(__name__)
CORS(app)

try:
	with open('/home/pi/Assignment_Two/config.json', 'r') as f:
		configuration = json.load(f)
except Exception:
	with open('Assignment_Two/config.json', 'r') as f:
		configuration = json.load(f)
try:		
	app.secret_key = configuration['SECRET_KEY']
	API_ACCESS_KEY = configuration['API_ACCESS_KEY']
	URL = configuration['URL']
except Exception as e:	raise
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#HOME PAGE
@app.route('/')
def home():
	"""The home page for practitioners"""

	return render_template('home.html')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#VIEW PATIENT FILE - initial page
@app.route('/viewPatientFile')
def viewPatientRecordsLanding():
	"""The function for the initial page for the view patients file feature"""

	doctor_list = []

	form1, form2 = DVPForm1(request.form), DVPForm2(request.form)

	if form1.errors: flash(form1.errors)
	if form2.errors: flash(form2.errors)

	try: doctor_list = getDoctorForList()
	except: flash("Error getting doctors for list.")

	return render_template('view_patient_file.html', form1=form1, form2=form2, doctor_list=doctor_list)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#VIEW PATIENT FILE - load data of selected patient
@app.route('/viewPatientFile', methods=['POST'])
def viewPatientRecordsGet():
	"""This function prepares and displays the data regarding the patient selected in the intitial page."""

	doctor_list = []
	data = []

	doctorExists = False
	form1, form2 = DVPForm1(request.form), DVPForm2(request.form)

	if form1.errors: flash(form1.errors)
	if form2.errors: flash(form2.errors)

	try: doctor_list = getDoctorForList()
	except: flash("Error getting doctors for list.")
	
	try:	selectedDoctorName = request.form['doctor'].split(" - ")[0]
	except: flash("A field was not detected. Source may be corrupt.")

	for doc in doctor_list:
		if doc['titleName'] == selectedDoctorName:	doctorExists = True
	
	try:
		if (request.form['doctor'] != None or request.form['doctor'] != "") and doctorExists == True:
			try:	
				data, errors = getRecordsData(request.form['pid'])
				for e in errors: flash(e)
				fullname = data[0]['patient_name']
				return render_template('view_patient_file.html', tempDoctor=request.form['doctor'], data=data, 
					form1=form1, form2=form2, pid=request.form['pid'], fullname=fullname, doctor_list=doctor_list, 
					selectedDoctor=selectedDoctorName)
			except:	
				flash("No records retrieved.")
				return render_template('view_patient_file.html', form1=form1, form2=form2, doctor_list=doctor_list, 
					selectedDoctor=request.form['doctor'])
		else:	flash("Doctor was not selected. Please select a doctor before making any requests.")
	except: flash("A field was not detected. Source may be corrupt.")

	return render_template('view_patient_file.html', form1=form1, form2=form2, doctor_list=doctor_list)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#FUNCTION TO GET PATIENT RECORDS
def getRecordsData(patient_id):
	"""This function fetches the records of a given patient."""

	errors, data = [], None

	if (patient_id != None and patient_id != ""):
		try:sendData = {'API_ACCESS_KEY': API_ACCESS_KEY, 'pid' : patient_id}
		except:	errors.append("Error preparing form data to send")

		try:
			getPatientRecords = requests.post(URL+"GetPatientRecords", data=sendData) #URL ------------------------
			data = getPatientRecords.json()
		except Exception as e:	errors.append("Error sending/receiving request" + str(e))
	else:	errors.append("Patient ID is blank. Fill form in appropriately.")

	return data, errors
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#FUNCTION TO GET DOCTORS LIST
def getDoctorForList():
	"""This function gets exisiting doctors to form a list of doctors to choose from."""

	doctor_list, doctor = [], {}

	try:
		getDoctors = requests.post(URL+"GetDoctors", data={'API_ACCESS_KEY': API_ACCESS_KEY}) #URL ------------------------
		data  = getDoctors.json()
	except:	return

	for x in range(len(data)):	doctor_list.append({ 'titleName' : data[x]["title"] + "." + data[x]["full_name"], 'id' : data[x]["doctor_id"] })

	return doctor_list
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#SUBMIT PATIENT RECORDS - send post request
@app.route('/submitSuccessfull', methods=['POST'])
def submitPatientRecordsAction():
	"""This page renders a view with the added notes/diagnosis if they were successful. Else it 
	re-renders with temporary data incase user made error."""

	message, note, diagnosis, fullname, selectedDoctorName = "", "", "", "", ""
	form1, form2 = DVPForm1(request.form), DVPForm2(request.form)
	noteAdded, diagnosisAdded, doctorExists = False, False, False
	doctor_list, data = getDoctorForList(), []

	if form1.errors: flash(form1.errors)
	if form2.errors: flash(form2.errors)

	try:
		#Validate doctor
		if (request.form['tempDoctor'] != None or request.form['tempDoctor'] != ""):
			
			try:
				selectedDoctorName = request.form['tempDoctor'].split(" - ")[0]
				selectedDoctorID = request.form['tempDoctor'].split(" - ")[1]
				for doc in doctor_list:
					if doc['titleName'] == selectedDoctorName:	doctorExists = True
			except: flash("Doctor object not as expected. Contact system admin.")
	except: pass

	try:	tempPid = request.form['tempPID']
	except: tempPid = ""
	
	if doctorExists == True:
		try:	
			#Validate Note
			if (request.form['addNote'] != None and request.form['addNote'] != ""):
				try: patientData = {'API_ACCESS_KEY': API_ACCESS_KEY, 'pid' : tempPid}
				except:	flash("Error preparing note data to send")

				try:
					patient = requests.post(URL+"GetPatient", data=patientData) #URL ------------------------
					patientResponse = patient.json()
					patientName = patientResponse['full_name']
				except Exception as e:
					flash("Patient name unobtainable." + str(e))

				try:
					sendNoteData = {
						'API_ACCESS_KEY': API_ACCESS_KEY,
						'patient_id' : tempPid,
						'entry_type' : 'Note',
						'value' : request.form['addNote'],
						'patient_name' : patientName,
						'doctor_name' : selectedDoctorName,
						'doctor_id' : selectedDoctorID
					}
				except: flash("Error preparing note data to send")

				try:
					addNoteToEntries = requests.post(URL+"AddPatientRecord", data=sendNoteData) #URL ------------------------
					addResponse = addNoteToEntries.json()
					if addResponse == None or addResponse == "null" or addResponse =="":	noteAdded = True
					else:	
						flash(str(addNoteToEntries.text))
						note = request.form['addNote']
				except Exception as e:	flash("Error sending request" + str(e))
		except: pass

		try:
			#Validate Diagnosis
			if (request.form['addDiagnosis'] != None or request.form['addDiagnosis'] != ""):
				try: patientData = {'API_ACCESS_KEY': API_ACCESS_KEY, 'pid' : tempPid}
				except: flash("Error preparing Diagnosis data to send")

				try:
					patient = requests.post(URL+"GetPatient", data=patientData) #URL ------------------------
					patientResponse = patient.json()
					patientName = patientResponse['full_name']
				except Exception as e: flash("Patient name not provide, Error obtaining using patient ID provided." + str(e))

				try:
					sendDiagnosisData = {
						'API_ACCESS_KEY': API_ACCESS_KEY,
						'patient_id' : tempPid,
						'entry_type' : 'Diagnosis',
						'value' : request.form['addDiagnosis'],
						'patient_name' : patientName,
						'doctor_name' : selectedDoctorName,
						'doctor_id' : selectedDoctorID
					}
				except Exception: flash("Error preparing diagnosis data to send")

				try:
					addDiagnosisToEntries = requests.post(URL+"AddPatientRecord", data=sendDiagnosisData) #URL ------------------------
					addResponse = addDiagnosisToEntries.json()
					if addResponse == None or addResponse == "null" or addResponse =="":	diagnosisAdded = True
					else: 
						flash(str(addDiagnosisToEntries.text))
						diagnosis = request.form['addDiagnosis']
				except Exception as e: flash("Error sending request" + str(e))
		except: pass

		data, errors = getRecordsData(tempPid)
		if len(data) == 0 or data == None:	data = []
		else:	fullname = data[0]['patient_name']

		for x in errors:	flash(x)
	
		if noteAdded == True and diagnosisAdded == True:	message = "Note and Diagnosis added. See updated records below."	
		if noteAdded == True and diagnosisAdded == False:	message = "Note added. See updated records below."	
		if noteAdded == False and diagnosisAdded == True:	message = "Diagnosis added. See updated records below."	
		if noteAdded == False and diagnosisAdded == False:	flash("Failed to submit. Ensure fields aren't blank. Otherwise contact system admin.")
	else: flash("The doctor selected is not on record!")

	return render_template('view_patient_file.html', tempDoctor=request.form['tempDoctor'], selectedDoctor=selectedDoctorName, doctor_list=doctor_list, data=data, form1=form1, form2=form2, custom_message=message, pid=tempPid, note=note, diagnosis=diagnosis, fullname=fullname)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#DOCTOR STATES AVAILABILITY -initial page
@app.route('/stateAvailability')
def stateAvailability():
	"""This function prepares the initial page for the state availability feature."""

	form = SAForm(request.form)
	if form.errors: flash(form.errors)

	doctor_list = getDoctorForList() #Make a lib, and import it for getDoctorForList etc.

	return render_template('state_availability.html', form=form, doctor_list=doctor_list)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#DOCTOR STATES AVAILABILITY - send availabilities
@app.route('/stateAvailability', methods=['POST'])
def stateAvailabilitySubmit():
	"""This page sends the data given in the initial page to create the event in google calendar. Re-rendering with the new
	calendar elements if successful, otherwise rendering the initial page again."""

	nameBlank = False
	startTimeBlank = False
	endTimeBlank = False
	startDateBlank = False
	endDateBlank = False
	doctorValid = False
	datelist = []
	responses = []

	form = SAForm(request.form)
	if form.errors: flash(form.errors)

	doctor_list = getDoctorForList() #Make a lib, and import it.

	try:
		#Validate form data
		if (request.form['doctor'] == None or request.form['doctor'] == ""):
			nameBlank = True
			flash("Doctor name left blank!")
		else:
			for doc in doctor_list:
				if request.form['doctor'] == doc['titleName']:	doctorValid = True
		if (request.form['startTime'] == None or request.form['startTime'] == ""):
			startTimeBlank = True
			flash("Start time is blank")
		if (request.form['endTime'] == None or request.form['endTime'] == ""):
			endTimeBlank = True
			flash("End time is blank")
		if (request.form['startDate'] == None or request.form['startDate'] == ""):
			startDateBlank = True
			flash("Start date is blank")
		if (request.form['endDate'] == None or request.form['endDate'] == ""):
			endDateBlank = True
			responses.append("Note: End date is blank")
	except: flash("A field was not detected. Source may be corrupt.")

	#Send addEvent request
	if (nameBlank == False and doctorValid == True and startTimeBlank == False and 
		endTimeBlank == False and startDateBlank == False):

		#invalid date param
		if dateutil.parser.parse(request.form['startDate']).date() < datetime.datetime.now().date():
			flash("Start date can not be in the past!")
		else:
			#if for one given day
			if endDateBlank == True:
				dateFrom = dateutil.parser.parse(request.form['startDate'])
				datelist.append(dateFrom)
			#if for a range of days
			else:
				dateFrom = dateutil.parser.parse(request.form['startDate'])
				dateTo = dateutil.parser.parse(request.form['endDate'])

				while dateFrom <= dateTo:
					datelist.append(dateFrom)
					dateFrom += datetime.timedelta(days=1)

		#prepare and send request for each date	
		for date in datelist:
			try:
				sendEventData = {
					'API_ACCESS_KEY': API_ACCESS_KEY,
					'name' : request.form['doctor'],
					'location' : 'Maps-Clinic: 9 Jerald Rd, Sunrise, Vic',
					'description' : 'Seeing Patients',
					'dateOnly' : datetime.datetime.strftime(date.date(), "%Y-%m-%d"),
					'start_time' : request.form['startTime'],
					'end_time' : request.form['endTime']
				}
			except:	flash("Error preparing event data to send")

			try:
				submitEvent = requests.post(URL+"addEvent", data=sendEventData) #URL ------------------------
				response = submitEvent.json()
			except Exception as e:	flash("Error sending request" + str(e))
			try:
				if response['Code'] == 400:
					flash(response['Message'])
				else:	responses.append(response['Message'])
			except:	flash("Response handling issue present")
	else:
		if doctorValid == False:	flash("Doctor Invalid!")

	return render_template('state_availability.html', form=form, doctor_list=doctor_list, responses=responses)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#RUN PROGRAM
if __name__ == '__main__':
	try:
		ip_address = os.popen('hostname -I').read().split(" ")
		app.run(host = ip_address[0], port=5003, debug=True)
	except:
		print("Error executing app.run with hostname -I")
		try:
			ip_address = socket.gethostname()
			app.run(host = ip_address, port=5003, debug=True)
		except:
			print("Error aqcuiring host ip address via socket and executing app.run")
			try:
				ip_address = os.popen('hostname -i').read()
				app.run(host = ip_address, port=5003, debug=True)
			except:	print("Could not run app.run at all!")
