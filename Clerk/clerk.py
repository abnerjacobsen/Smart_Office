#!/usr/bin/env python3

""" Clerk webservice for MAPS 
Here the clerk's can make bookings, cancel bookings, 
view patients seen for a period, add a doctor and remove a doctor
and view doctors."""


import datetime
import json
import os
import socket
import time
from functools import wraps

import dateutil.parser
import pygal
import requests
from flask import *
from flask_wtf import *

from Forms.Forms import *

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

#HOME PAGE
@app.route('/')
def admin():
	"""Home page for clerks"""

	return render_template('home.html')
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#BOOK AN APPOINTMENT - Initial
@app.route('/book_appointment')
def bookAppointment():
	"""Book an appointment initial page.
	This function will render the initial page with doctor list and calendar"""
	
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
		titleName = data[x]["title"] + "." + data[x]["full_name"]
		doctor_list.append(titleName)

	return render_template('book_appointment.html', form1=form1, form2=form2, doctor_list=doctor_list)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#BOOK AN APPOINTMENT - After date and doctor have been selected
@app.route('/book_appointment', methods=['POST'])
def bookAppointmentPrepare():
	"""Book an appointment to see a doctor.
	This function will render the booking page with the available times for the
	doctor on the day selected"""

	data = []
	doctor_list = []
	getAvailableTimes = []
	notifications = []
	selectedDoctor = None
	selectedDate = None
	enteredPID = None

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
		if request.form['pid']:	enteredPID = request.form['pid']
		if request.form['date']:	selectedDate =  request.form['date']
		if request.form['doctor']:	selectedDoctor = request.form['doctor']
	except:	
		flash("A field was not detected. Source may be corrupt.")
		return render_template('book_appointment.html', form1=form1, form2=form2, doctor_list=doctor_list, notifications=notifications)

	if selectedDoctor and selectedDate and enteredPID:
		try:
			sendData1 = {
				'API_ACCESS_KEY': API_ACCESS_KEY,
				'date' : request.form['date'],
				'doctor' : request.form['doctor']
			}
		except:	flash("Error preparing form data to send to get available times.")

		try:	getAvailableTimes = requests.post(URL+"GetAvailableTimes", data=sendData1) #URL ------------------------
		except:	flash("Error sending request")
		
		try:
			response  = getAvailableTimes.json()
			availableTimes = json.loads(response)
		except Exception as e:	flash("Error handling response data json()" + str(e))

		try:
			earliestAppt = selectedDate + " " + availableTimes[0]
			latestAppt = selectedDate + " " + availableTimes[len(availableTimes)-1]
		except:	flash("couldn't prepare time params")

		try:
			sendData2 = {
				'API_ACCESS_KEY': API_ACCESS_KEY,
				'doctorName' : selectedDoctor,
				'apptsFrom' : earliestAppt,
				'apptsTo' : latestAppt
			}
		except:	flash("Error preparing form data to send")

		try:	getAllPatientAppts = requests.post(URL+"GetAllAppointments", data=sendData2) #URL ------------------------
		except Exception as e:	flash("Error sending request" + str(e))

		try:	data  = getAllPatientAppts.json()
		except:	flash("Error handling response data json()")

		if len(data) > 0:
			for item in data:
				try:
					time = dateutil.parser.parse(item['date_time'])
					if str(time.time()) in availableTimes:
						availableTimes.remove(str(time.time()))
				except:	flash("error removing existing appointment times")

		try:	return render_template(	'book_appointment.html', desiredDate=selectedDate, patientID=enteredPID, 
									doctorToSee=selectedDoctor, availableTimes=availableTimes, selectedDoctor=selectedDoctor, 
									selectedDate=selectedDate, enteredPID=enteredPID, form1=form1, form2=form2, 
									doctor_list=doctor_list, notifications=notifications
									)
		except:	return render_template(	'book_appointment.html', selectedDoctor=selectedDoctor, 
									selectedDate=selectedDate, enteredPID=enteredPID, form1=form1, 
									form2=form2, doctor_list=doctor_list, notifications=notifications
									)
	else:
		if not enteredPID:	flash("Patient ID is blank. Fill form in appropriately.") 
		if not selectedDate:	flash("Date is blank. Fill form in appropriately.")
		if not selectedDoctor:	flash("Doctor was not selected. Fill form in appropriately.")

		return render_template('book_appointment.html', selectedDoctor=selectedDoctor, selectedDate=selectedDate, 
								enteredPID=enteredPID, form1=form1, form2=form2, doctor_list=doctor_list, notifications=notifications)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#BOOK AN APPOINTMENT - Post the appointment
@app.route('/book_appointment_send', methods=['POST'])
def bookAppointmentAction():
	"""Book an appointment to see a doctor.
	This function will render the page after the post request to
	make the booking has been sent. It will either render with a success message, 
	or flash some errors so the user may retry."""

	data = []
	doctor_list = []
	notifications = []
	selectedDoctor = None
	selectedDate = None
	enteredPID = None
	
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
		if request.form['pidTwo']:	enteredPID = request.form['pidTwo']
		if request.form['desiredDate']:	selectedDate =  request.form['desiredDate']
		if request.form['doctorToSee']:	selectedDoctor = request.form['doctorToSee']
		if request.form['time']:	selectedTime = request.form['time']	
	except:	
		flash("A field was not detected. Source may be corrupt.")
		return render_template('book_appointment.html', form1=form1, form2=form2, doctor_list=doctor_list, notifications=notifications)

	if selectedDoctor and selectedDate and enteredPID and selectedTime:
		dateToSend = str(selectedDate) + " " + str(selectedTime)
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
				if int(tempTime[0]) >= 12:
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
		except:	return render_template(	'book_appointment.html', form1=form1, form2=form2, notifications=notifications)
	else:
		if not enteredPID:	flash("Patient ID is blank. Fill form in appropriately.") 
		if not selectedDate:	flash("Date is blank. Fill form in appropriately.")
		if not selectedDoctor:	flash("Doctor was not selected. Fill form in appropriately.")

		return render_template('book_appointment.html', selectedDoctor=selectedDoctor, selectedDate=selectedDate, 
								enteredPID=enteredPID, form1=form1, form2=form2, doctor_list=doctor_list, notifications=notifications)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#CANCEL APPOINTMENT - Initial
@app.route('/cancel_appointment')
def cancelAppointment():
	"""This function will render the initial cancel appointment page"""

	form = CancelApptForm(request.form)
	if form.errors: flash(form.errors)

	return render_template('cancel_appointment.html', form=form)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#CANCEL APPOINTMENT - After patient id has been entered
@app.route('/cancel_appointment', methods=['POST'])
def cancelAppointmentAction():
	"""This function will get all appointments for the patient id provided
	and render them to the page in the form of a table"""

	pid = ""
	errors = []
	data = []
	pName = ""

	form = CancelApptForm(request.form)
	if form.errors: errors.append(form.errors)
	try:
		if request.form['pid'] and request.form['pid'] != "":
			pid = request.form['pid']
			try:
				sendData = {
					'API_ACCESS_KEY': API_ACCESS_KEY,
					'pid' : pid
				}
			except:	errors.append("Error preparing form data to send")

			try:	getPatientApptsRequest = requests.post(URL+"GetPatientAppointments", data=sendData) #URL ------------------------
			except Exception as e:	errors.append("Error sending request" + str(e))
			
			try:	
				data  = getPatientApptsRequest.json()
				pName = data[0]['patient_name']
			except:	errors.append("No Appointments Rertreived!")
		else:	errors.append("Patient ID is blank. Fill form in appropriately.") 
	except:	errors.append("A field was not detected. Source may be corrupt.")

	return render_template('cancel_appointment.html', pName=pName, form=form, data=data, p_id=pid, errors=errors)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#CANCEL APPOINTMENT - Send delete request
@app.route('/cancel_appointment', methods=['DELETE'])
def cancelAppointmentActionDelete():
	"""This function will post the delete request and re-render the page with
	either a success message or flash errors so the user may retry"""

	pid = ""
	dataGetResponse = None
	errors = []
	data = []

	form = CancelApptForm(request.form)
	if form.errors: errors.append(form.errors)
	
	try:
		if (request.form['apptID'] != None and request.form['apptID'] != ""):
			try:
				sendDataDel = {
					'API_ACCESS_KEY': API_ACCESS_KEY,
					'apptID' : request.form['apptID']
				}
			except:	errors.append("Error preparing form data to send")

			try:	deletePatientApptsRequest = requests.post(URL+"DeletePatientAppointment", data=sendDataDel) #URL ------------------------
			except Exception as e:	errors.append("Error sending request" + str(e))

		if (request.form['pid'] != None and request.form['pid'] != ""):
			pid = request.form['pid']
			try:
				sendDataGet = {
					'API_ACCESS_KEY': API_ACCESS_KEY,
					'pid' : pid
				}
			except:	errors.append("Error preparing form data to send")

			try:	getPatientApptsRequest = requests.post(URL+"GetPatientAppointments", data=sendDataGet) #URL ------------------------
			except Exception as e:	errors.append("Error sending request" + str(e))
			
			try:	dataGetResponse  = getPatientApptsRequest.json()
			except:	errors.append("Error handling response data json()")
		else:	errors.append("Patient ID is blank. Fill form in appropriately.") 
	except:	errors.append("A field was not detected. Source may be corrupt.")
		 
	return render_template('cancel_appointment.html', form=form, data=dataGetResponse, p_id=pid, errors=errors)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#VISUALISE PATIENTS SEEN - initial page
@app.route('/view_patients_seen')
def viewPatientsSeen():
	""" This function is the initial view for the view patients seen page """

	doctor_list = []
	data = []

	form = VPSForm(request.form)
	if form.errors: flash(form.errors)

	try:
		getDoctors = requests.post(URL+"GetDoctors", data={'API_ACCESS_KEY': API_ACCESS_KEY}) #URL ------------------------
		data  = getDoctors.json()
	except:	flash("Error with request")

	for x in range(len(data)):
		try: doctor_list.append(data[x]["title"] + "." + data[x]["full_name"])
		except: flash("Error loading in doctor")
		
	try:
		#Graph type: Bar Graph
		graph = pygal.Bar()
		graph.title = "Patients Seen Will Show Here"
	except:	flash("Error assigning graph type")

	#Render graph
	try:	graph_data = graph.render_data_uri()
	except:	flash("Error rendering graph")

	return render_template('view_patients_seen.html', form=form, doctor_list=doctor_list, graph_data=graph_data)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#VISUALISE PATIENTS SEEN - get data and display it
@app.route('/view_patients_seen', methods=['POST'])
def viewPatientsSeenAction():
	""" After user has input a date choice, then this function fetches all the data required to view on the page"""

	allResults = []
	doctor_list = []
	statistics = []
	graphHeading = ""
	endDate, startDate = None, None

	form = VPSForm(request.form)
	if form.errors: flash(form.errors)

	try:
		getDoctors = requests.post(URL+"GetDoctors", data={'API_ACCESS_KEY': API_ACCESS_KEY}) #URL ------------------------
		data  = getDoctors.json()
	except:	flash("Error with request")
	
	for x in range(len(data)):
		try: doctor_list.append(data[x]["title"] + "." + data[x]["full_name"])
		except: flash("Error loading in doctor")

	try:
		#Graph type: Bar Graph
		graph = pygal.Bar()
		graph.title = "Patients Seen Will Show Here"
	except:	flash("Error assigning graph type")

	try:
		if (request.form['week'] != None):
			endDate = datetime.datetime.now()
			startDate = endDate - datetime.timedelta(days=7)
		else:	flash("week NOT checked!")
	except:	pass

	try: 
		if (request.form['month'] != None):
			endDate = dateutil.parser.parse(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
			startDate = endDate - datetime.timedelta(days=31)
		else:	flash("month NOT checked!")
	except:	pass

	try: 
		if ((request.form['startDate'] != None and request.form['startDate'] != "") and 
			(request.form['endDate'] != None and request.form['endDate'] != "")):

			endDate = dateutil.parser.parse(request.form['endDate'])
			startDate = dateutil.parser.parse(request.form['startDate'])
		else:	flash("Manual Date NOT Entered!")
	except:	pass

	if ((startDate != None and startDate != "") and (endDate != None and endDate != "")):
		graphHeading = "Patients Seen For All Doctors" + "\n\n" + "From [" + str(startDate) + "] to [" + str(endDate) + "]\n"
		
		for doc in doctor_list:
			graphData = []
			xLabels = []
			dateTimeArr = []
			result = []
			doctorExists = False

			try:
				selectedDocWithTitle = doc
				selectedDoctorFullName = selectedDocWithTitle.split(".")[1]
			except:
				flash("Selected doctor input was invalid")
				selectedDoctorFullName = ""

			try:	
				for x in range(len(data)): 
					if selectedDoctorFullName == data[x]["full_name"]:
						doctorExists = True
			except:	flash("Can not search for " + str(doc) + ". Data corrupt, contact system admin.")
			
			if doctorExists == True:
				if startDate <= endDate:
					try:
						getApptsForPeriod = requests.post(URL+"GetPatientsSeen", 
											data={'API_ACCESS_KEY': API_ACCESS_KEY, 
											'doctor' : doc, 
											'startDate' : startDate, 
											'endDate' : endDate}) #URL ------------------------^
						result = getApptsForPeriod.json()
					except:	flash("Error Load Data For: " + str(doc))
						
					diff = endDate - startDate

					if diff.days > 1:
						for x in result:	dateTimeArr.append(str(dateutil.parser.parse(x['date_time']).date()))

						for i in range(diff.days+1):
							nextXvariable = startDate + datetime.timedelta(days=i)
							xLabels.append(str(nextXvariable.date()))
							graphData.append(dateTimeArr.count(str(nextXvariable.date())))

					elif diff.seconds > 3600:
						for x in result:	dateTimeArr.append(str(dateutil.parser.parse(x['date_time']).time()))

						for i in range(int(diff.seconds/3600) +1):
							nextXvariable = startDate + datetime.timedelta(seconds=i*3600)
							xLabels.append(str(nextXvariable.time()))
							graphData.append(dateTimeArr.count(str(nextXvariable.time())))
					else:
						for x in result:	dateTimeArr.append(str(dateutil.parser.parse(x['date_time']).minute))

						for i in range(int(diff.seconds/60)):
							nextXvariable = startDate + datetime.timedelta(seconds=i*60)
							if nextXvariable.minute not in xLabels:
								xLabels.append(str(nextXvariable.minute))
								graphData.append(dateTimeArr.count(str(nextXvariable.minute)))
							else:	pass
					
					busiestSegment, slowestSegment = xLabels[graphData.index(max(graphData))], xLabels[graphData.index(min(graphData))]
					count = sum(graphData)
					stat = {
						'doctor' : doc,
						'maxBusy' : busiestSegment,
						'minBusy' : slowestSegment,
						'totalSeen' : count
					}
					statistics.append(stat)
				else:
					graphHeading = "Invalid Input: ie: Start Date is AFTER End Date or date format is incorrect"
					break
			else:	flash(str(doc) + " Could Not Be Found In The Database")

			try:	graph.add(doc, graphData)
			except Exception as e:	flash("Error adding " + str(doc) + " graph data : " + str(e))
			if result :	allResults.append(result)
		#END OF FOR LOOP
	else:	flash("Date Error!")

	#Prepare graph
	try:	graph.title = graphHeading
	except:	flash("Error assigning graph title")
	#Assign x labels
	try:	graph.x_labels = xLabels
	except Exception as e:	flash("Error adding x labels to graph : " + str(e))
	#Render graph
	try:	graph_data = graph.render_data_uri()
	except:	flash("Error rendering graph")
	
	return render_template('view_patients_seen.html', form=form, doctor_list=doctor_list, 
			graph_data=graph_data, results=allResults, statistics=statistics)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#REMOVE DOCTOR - initial page
@app.route('/remove_doctor')
def removeDoctorPopulatePage():
	"""This is the function that prepares the initial view for the Remove Doctors Page"""

	doctor_list = []

	form = rmDocForm(request.form)
	if form.errors: flash(form.errors)

	try:
		getDoctors = requests.post(URL+"GetDoctors", data={'API_ACCESS_KEY': API_ACCESS_KEY}) #URL ------------------------
		data  = getDoctors.json()
	except:	flash("Error with request")
	
	for x in range(len(data)):
		try: doctor_list.append(data[x]["title"] + "." + data[x]["full_name"])
		except: flash("Error loading in doctor")

	return render_template('remove_doctor.html', form=form, doctor_list=doctor_list)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#REMOVE DOCTOR - send delete request
@app.route('/remove_doctor', methods=['POST'])
def removeDoctorAction():
	"""This function attempts to remove the doctor chosen in the initial page"""

	reply = ""
	doctor_list = []

	form = rmDocForm(request.form)
	if form.errors: flash(form.errors)

	try:
		#Validate doctor and doctor ID
		if request.form['doctor'] != None and request.form['doctor'] != "":
			try:
				doctorName = request.form['doctor'].split('.')[1]
				rmDocRequest = requests.post(URL+"DeleteDoctor", data={'API_ACCESS_KEY': API_ACCESS_KEY, 'doctorName' : doctorName}) #URL ------------------------
				reply = rmDocRequest.json()
			except:	flash("error with remove doctor request")
		else:	flash("Error: A doctor was not selected.")
	except:	flash("A field was not detected. Source may be corrupt.")
	
	time.sleep(3)
	#Create new doctor list AFTER removing doctor
	try:
		getDoctors = requests.post(URL+"GetDoctors", data={'API_ACCESS_KEY': API_ACCESS_KEY}) #URL ------------------------
		data  = getDoctors.json()
	except:	flash("Error with request")
	
	for x in range(len(data)):
		try: doctor_list.append(data[x]["title"] + "." + data[x]["full_name"])
		except: flash("Error loading in doctor")

	return render_template('remove_doctor.html', form=form, doctor_list=doctor_list, response=reply)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#ADD DOCTOR - initial page
@app.route('/add_doctor')
def addDoctor():
	"""This is the function that prepares the initial page of Add Doctor"""

	form = addDocForm(request.form)
	if form.errors: flash(form.errors)

	return render_template('add_doctor.html', form=form)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#ADD DOCTOR - send post request
@app.route('/add_doctor', methods=['POST'])
def addDoctorAction():
	"""This function attempts the add the doctor details to the database"""

	reply = ""	

	form = addDocForm(request.form)
	if form.errors: flash(form.errors)
	try:
		if((request.form['doctorID'] != None and request.form['doctorID'] != "") and
		(request.form['doctorTitle'] != None and request.form['doctorTitle'] != "") and
		(request.form['doctorFN'] != None and request.form['doctorFN'] != "") and
		(request.form['phone_number'] != None and request.form['phone_number'] != "") and
		(request.form['specialty'] != None and request.form['specialty'] != "") and
		(request.form['regular_room'] != None and request.form['regular_room'] != "")):

			doctor_id = request.form['doctorID']
			title = request.form['doctorTitle']
			full_name = request.form['doctorFN']
			phone_number = request.form['phone_number']
			specialty = request.form['specialty']
			regular_room = request.form['regular_room']

		else:	flash("All fields required")
		
		try:
			dataToSend = {'API_ACCESS_KEY': API_ACCESS_KEY, 
						'doctor_id' : doctor_id, 'title' : title,  
						'full_name' : full_name, 'phone_number' : phone_number, 
						'specialty' : specialty, 'regular_room' : regular_room 
						}
		except:	flash("Error loading request data. Contact system admin")
		
		try:
			addDocRequest = requests.post(URL+"AddDoctor", data=dataToSend) #URL ------------------------
			reply = addDocRequest.json()
		except:	flash("error with add doctor request")
	except:	flash("A field was not detected. Source may be corrupt.")

	return render_template('add_doctor.html', form=form, response=reply)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#VIEW DOCTORS
@app.route('/view_doctors')
def viewDoctors():
	"""This function retrieves all doctor records and displays them"""

	data, errors = [], []
	try:
		getDoctors = requests.post(URL+"GetDoctors", data={'API_ACCESS_KEY': API_ACCESS_KEY}) #URL ------------------------
		data  = getDoctors.json()
	except Exception as e:	errors.append(str(e))

	return render_template('view_doctors.html', data=data)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#RUN PROGRAM
if __name__ == '__main__':
	try:
		ip_address = os.popen('hostname -I').read().split(" ")
		app.run(host = ip_address[0], port=5002, debug=True)
	except:
		print("Error executing app.run with hostname -I")
		try:
			ip_address = socket.gethostname()
			app.run(host = ip_address, port=5002, debug=True)
		except:
			print("Error aqcuiring host ip address via socket and executing app.run")
			try:
				ip_address = os.popen('hostname -i').read()
				app.run(host = ip_address, port=5002, debug=True)
			except:
				print("Could not run app.run at all!")
