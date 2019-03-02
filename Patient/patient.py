#!/usr/bin/env python3

""" Patient webservice for MAPS 
Here the Patient's can make bookings, cancel bookings, 
and register"""

import datetime
import json
import os
import random
import socket
import sqlite3
import time
from functools import wraps

import dateutil.parser
import pygal
import requests
from flask import Flask, flash, render_template, request

from Forms.Forms import BookApptForm1, BookApptForm2, CancelApptForm, registerForm

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

app = Flask(__name__)
app.config.from_object(__name__)

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

#HOME
@app.route('/')
def admin():
	"""The Home page for patients"""

	return render_template('home.html')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#REGISTER
@app.route('/patient_registration')
def patientRegistration():
	"""Patient registration page"""
	
	form = registerForm(request.form)
	if form.errors: flash(form.errors)
	
	return render_template('patient_registration.html', form=form)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@app.route('/patient_registration', methods=['POST'])
def patientRegistrationAction(): 
	"""Patient registration action page"""
	
	form = registerForm(request.form)
	if form.errors: flash(form.errors)
	try:
		if ((request.form['patientTitle'] != None and request.form['patientTitle'] != "") and
			(request.form['patientFN'] != None and request.form['patientFN'] != "") and
			(request.form['phone_number'] != None and request.form['phone_number'] != "")):

			try:
				GetNewPatientID = requests.post(URL+"GetNewPatientID", data={'API_ACCESS_KEY': API_ACCESS_KEY}) #URL ------------------------
				data = GetNewPatientID.json()
			except:	flash("ERROR ASSIGNING NEW PATIENT ID. PLEASE CONTACT US FOR HELP.")

			newPatientData = {
				'API_ACCESS_KEY': API_ACCESS_KEY,
				'patientID' : data,
				'patientTitle' : request.form['patientTitle'],
				'patientFN' : request.form['patientFN'],
				'phone_number' : request.form['phone_number']
			}

			try:
				submitNewPatientReg = requests.post(URL+"AddPatient", data=newPatientData) #URL ------------------------
				message = submitNewPatientReg.json()
				if message == None or message == "null" or message =="":
					return render_template('registration_complete.html', title=request.form['patientTitle'], fullname=request.form['patientFN'], id=data)
				else:
					flash(str(submitNewPatientReg.text))
					return render_template('patient_registration.html', form=form)
			except Exception:
				flash("Please fill in the fields appropriately, or contact us for help.")
				return render_template('patient_registration.html', form=form)
		else:
			flash("One Or More Fields Were Left Blank. Please fill in all fields")
			return render_template('patient_registration.html', form=form)
	except:
		flash("A field was not detected. Source may be corrupt.")
		return render_template('patient_registration.html', form=form)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#BOOK AN APPOINTMENT
@app.route('/book_appointment')
def bookAppointment():
	"""Patient book appoitnment page"""
	
	doctor_list = []

	form1, form2 = BookApptForm1(request.form), BookApptForm2(request.form)
	if form1.errors: flash(form1.errors)
	if form2.errors: flash(form2.errors)

	try:
		getDoctors = requests.post(URL+"GetDoctors", data={'API_ACCESS_KEY': API_ACCESS_KEY}) #URL ------------------------
		data  = getDoctors.json()
	except: flash("Failed to obtain doctors list")
	
	for x in range(len(data)):
		try: doctor_list.append(data[x]["title"] + "." + data[x]["full_name"])
		except: flash("Error loading in doctor")

	return render_template('book_appointment.html', form1=form1, form2=form2, doctor_list=doctor_list)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@app.route('/book_appointment', methods=['POST'])
def bookAppointmentPrepare():
	"""Patient book appointment page, rendered with available times after initial selection
	on previous page."""
	
	errors = []
	getAvailableTimes = []
	selectedDoctor = None
	selectedDate = None
	enteredPID = None
	doctor_list = []
	data = []
	
	form1, form2 = BookApptForm1(request.form), BookApptForm2(request.form)
	if form1.errors: flash(form1.errors)
	if form2.errors: flash(form2.errors)
	
	try:
		getDoctors = requests.post(URL+"GetDoctors", data={'API_ACCESS_KEY': API_ACCESS_KEY}) #URL ------------------------
		data  = getDoctors.json()
	except: flash("Failed to obtain doctors list")
	
	for x in range(len(data)):
		try: doctor_list.append(data[x]["title"] + "." + data[x]["full_name"])
		except: flash("Error loading in doctor")
	
	try:
		if (request.form['pid'] != None and request.form['pid'] != ""):	enteredPID = request.form['pid']
		if (request.form['date'] != None and request.form['date'] != ""):	selectedDate =  request.form['date']
		if (request.form['doctor'] != None and request.form['doctor'] != ""):	selectedDoctor = request.form['doctor']

		if selectedDoctor and selectedDate and enteredPID:
			try:
				sendData1 = {
					'API_ACCESS_KEY': API_ACCESS_KEY,
					'date' : request.form['date'],
					'doctor' : request.form['doctor']
				}
			except:	errors.append("Error preparing form data to send to get available times.")

			try:	getAvailableTimes = requests.post(URL+"GetAvailableTimes", data=sendData1) #URL ------------------------
			except:	errors.append("Error sending request")
			
			try:
				response  = getAvailableTimes.json()
				availableTimes = json.loads(response)
				errors.append(availableTimes)
			except Exception as e:	errors.append("Error handling response data json()" + str(e))

			try:
				earliestAppt = selectedDate + " " + availableTimes[0]
				latestAppt = selectedDate + " " + availableTimes[len(availableTimes)-1]
			except:	errors.append("couldn't prepare time params")

			try:
				sendData2 = {
					'API_ACCESS_KEY': API_ACCESS_KEY,
					'doctorName' : selectedDoctor,
					'apptsFrom' : earliestAppt,
					'apptsTo' : latestAppt
				}
			except:	errors.append("Error preparing form data to send")

			try:	getAllPatientAppts = requests.post(URL+"GetAllAppointments", data=sendData2) #URL ------------------------
			except Exception as e:	errors.append("Error sending request" + str(e))

			try:
				data  = getAllPatientAppts.json()
				errors.append(data)
			except:	errors.append("Error handling response data json()")

			if len(data) > 0:
				for item in data:
					try:
						time = dateutil.parser.parse(item['date_time'])
						errors.append(time.time())
						if str(time.time()) in availableTimes:	availableTimes.remove(str(time.time()))
					except:	errors.append("error removing existing appointment times")

			try:	return render_template(	'book_appointment.html', desiredDate=selectedDate, patientID=enteredPID, 
										doctorToSee=selectedDoctor, availableTimes=availableTimes, selectedDoctor=selectedDoctor, 
										selectedDate=selectedDate, enteredPID=enteredPID, form1=form1, form2=form2, 
										doctor_list=doctor_list, errors=errors
										)
			except:	return render_template(	'book_appointment.html', selectedDoctor=selectedDoctor, 
										selectedDate=selectedDate, enteredPID=enteredPID, form1=form1, 
										form2=form2, doctor_list=doctor_list, errors=errors
										)
		else:
			if not enteredPID:	errors.append("Patient ID is blank. Fill form in appropriately.") 
			if not selectedDate:	errors.append("Date is blank. Fill form in appropriately.")
			if not selectedDoctor:	errors.append("Doctor was not selected. Fill form in appropriately.")

			return render_template('book_appointment.html', selectedDoctor=selectedDoctor, selectedDate=selectedDate, enteredPID=enteredPID, form1=form1, form2=form2, doctor_list=doctor_list, errors=errors)
	except:
		flash("A field was not detected. Source may be corrupt.")
		return render_template('book_appointment.html', form1=form1, form2=form2, doctor_list=doctor_list)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@app.route('/book_appointment_send', methods=['POST'])
def bookAppointmentAction():
	"""Patient book appointment page rendered with confirmation or notification of
	booking success or failure respectfully."""
	
	notifications = []
	selectedDoctor = None
	selectedDate = None
	enteredPID = None
	doctor_list = []
	data = []
	
	form1, form2 = BookApptForm1(request.form), BookApptForm2(request.form)
	if form1.errors: flash(form1.errors)
	if form2.errors: flash(form2.errors)
	
	try:
		getDoctors = requests.post(URL+"GetDoctors", data={'API_ACCESS_KEY': API_ACCESS_KEY}) #URL ------------------------
		data  = getDoctors.json()
	except: flash("Failed to obtain doctors list")
	
	for x in range(len(data)):
		try: doctor_list.append(data[x]["title"] + "." + data[x]["full_name"])
		except: flash("Error loading in doctor")
	try:
		if (request.form['pidTwo'] != None and request.form['pidTwo'] != ""):	enteredPID = request.form['pidTwo']
		if (request.form['desiredDate'] != None and request.form['desiredDate'] != ""):	selectedDate =  request.form['desiredDate']
		if (request.form['doctorToSee'] != None and request.form['doctorToSee'] != ""):	selectedDoctor = request.form['doctorToSee']
		if (request.form['time'] != None and request.form['time'] != ""):	selectedTime = request.form['time']	

		if selectedDoctor and selectedDate and enteredPID and selectedTime:
			dateToSend = selectedDate + " " + selectedTime
			try:
				sendData1 = {
					'API_ACCESS_KEY': API_ACCESS_KEY,
					'date' : dateToSend,
					'doctor' : selectedDoctor,
					'pid' : enteredPID
				}
			except:	flash("Error preparing form data to send to get available times.")

			try:	bookApptReq = requests.post(URL+"BookAppointment", data=sendData1) #URL ------------------------
			except:	flash("Error sending request")
			
			try:	response  = bookApptReq.json()
			except Exception as e:	flash("Error handling response data json()" + str(e))

			try:	
				if response['patient_id']:
					splitDateTime = response['date_time'].split("T")[0].split("-")
					tDate = splitDateTime[2] + "/" + splitDateTime[1] + "/" + splitDateTime[0]
					tempTime = response['date_time'].split("T")[1].split("+")[0].split(":")
					if int(tempTime[0]) > 12:
						hour = str(int(tempTime[0]) - 12)
						AM_PM = "PM"
					else: 
						hour = tempTime[0]
						AM_PM = "AM"
					timeDisplay = str(hour) + ":" + str(tempTime[1]) + " " + str(AM_PM)

					notifications.append("Appt Booked For " + str(response['patient_name']) + " on " 
					+ tDate + " at " + timeDisplay + " with Practitioner " + response['doctor_name'])

			except Exception as e: flash("Failed to book appointment, response not received." + "Exception: " + str(e))

			try:	return render_template(	'book_appointment.html', form1=form1, form2=form2, 
										doctor_list=doctor_list, notifications=notifications
										)
			except:
				flash("dummy page  - something went wrong - doctorsList?")
				return render_template(	'book_appointment.html', notifications=notifications)
		else:
			if not enteredPID:	flash("Patient ID is blank. Fill form in appropriately.") 
			if not selectedDate: flash("Date is blank. Fill form in appropriately.")
			if not selectedDoctor:	flash("Doctor was not selected. Fill form in appropriately.")

			return render_template('book_appointment.html', selectedDoctor=selectedDoctor, selectedDate=selectedDate, enteredPID=enteredPID, form1=form1, form2=form2, doctor_list=doctor_list, notifications=notifications)
	except:
		flash("A field was not detected. Source may be corrupt.")
		return render_template('book_appointment.html', form1=form1, form2=form2, doctor_list=doctor_list)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#CANCEL APPOINTMENT - initial page
@app.route('/cancel_appointment')
def cancelAppointment():
	"""Patient cancel appointment page."""
	
	form = CancelApptForm(request.form)
	if form.errors: flash(form.errors)

	return render_template('cancel_appointment.html', form=form)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#CANCEL APPOINTMENT - get appointments to cancel from
@app.route('/cancel_appointment', methods=['POST'])
def cancelAppointmentAction():
	"""Patient Cancel appointment page rendered with confirmation window
	for if the patient is sure to delete this appointment."""
	
	pid = ""
	errors = []
	data = []

	form = CancelApptForm(request.form)
	if form.errors: errors.append(form.errors)
	try:
		if (request.form['pid'] != None and request.form['pid'] != ""):
			pid = request.form['pid']

			try:	sendData = {'API_ACCESS_KEY': API_ACCESS_KEY, 'pid' : pid}
			except:	errors.append("Error preparing form data to send")

			try:	getPatientApptsRequest = requests.post(URL+"GetPatientAppointments", data=sendData) #URL ------------------------
			except Exception as e:	errors.append("Error sending request" + str(e))
			
			try:	data  = getPatientApptsRequest.json()
			except Exception:	errors.append("Error handling response data json()")
		else:	errors.append("Patient ID is blank. Fill form in appropriately.") 
	except: errors.append("A field was not detected. Source may be corrupt.")

	return render_template('cancel_appointment.html', form=form, data=data, p_id=pid, errors=errors)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#CANCEL APPOINTMENT - send delete request
@app.route('/cancel_appointment', methods=['DELETE'])
def cancelAppointmentActionDelete():
	"""Patient cancel appointment page rendered with result of appointment
	cancellation (ie: success or failure)"""
	
	pid = ""
	dataGetResponse = None
	errors = []
	data = []

	form = CancelApptForm(request.form)
	if form.errors: errors.append(form.errors)
	try:
		if (request.form['apptID'] != None and request.form['apptID'] != ""):
			try:	sendDataDel = {'API_ACCESS_KEY': API_ACCESS_KEY, 'apptID' : request.form['apptID']}
			except:	errors.append("Error preparing form data to send")

			try:	deletePatientApptsRequest = requests.post(URL+"DeletePatientAppointment", data=sendDataDel) #URL ------------------------
			except Exception as e:	errors.append("Error sending request" + str(e))

		if (request.form['pid'] != None and request.form['pid'] != ""):
			pid = request.form['pid']
			try:sendDataGet = {'API_ACCESS_KEY': API_ACCESS_KEY, 'pid' : pid}
			except:	errors.append("Error preparing form data to send")

			try:	getPatientApptsRequest = requests.post(URL+"GetPatientAppointments", data=sendDataGet) #URL ------------------------
			except Exception as e:	errors.append("Error sending request" + str(e))
			
			try:	dataGetResponse  = getPatientApptsRequest.json()
			except:	errors.append("Error handling response data json()")
		else:	errors.append("Patient ID is blank. Fill form in appropriately.") 
	except: errors.append("A field was not detected. Source may be corrupt.")

	return render_template('cancel_appointment.html', form=form, data=dataGetResponse, p_id=pid, errors=errors)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#RUN PROGRAM
if __name__ == '__main__':
	try:
		ip_address = os.popen('hostname -I').read().split(" ")
		app.run(host = ip_address[0], port=5004, debug=True)
	except:
		print("Error executing app.run with hostname -I")
		try:
			ip_address = socket.gethostname()
			app.run(host = ip_address, port=5004, debug=True)
		except:
			print("Error aqcuiring host ip address via socket and executing app.run")
			try:
				ip_address = os.popen('hostname -i').read()
				app.run(host = ip_address, port=5004, debug=True)
			except:	print("Could not run app.run at all!")
