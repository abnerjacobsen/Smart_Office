"""This module contains all the forms for patients."""

from wtforms import validators, TextField, SelectField, Form

class BookApptForm1(Form):
    """This is form validation for preparing data for booking an appointment."""
    
    pid = TextField('Enter Patient ID:', validators=[validators.required(), validators.Length(min=6, max=6)])
    doctor = SelectField('Please select which doctor you wish to see:', validators=[validators.required()])
    date = SelectField('Please select a date:', validators=[validators.required()])

class BookApptForm2(Form):
    """This is form validation for actually booking the appointment."""
    
    pidTwo = TextField('Your ID: ', validators=[validators.required(), validators.Length(min=6, max=6)])
    doctorToSee = SelectField('Appointments for: ', validators=[validators.required()])
    desiredDate = SelectField('on date: ', validators=[validators.required()])
    time = SelectField('Available times:', validators=[validators.required()])

class CancelApptForm(Form):
    """This is form validation for cancelling an appointment."""
    
    pid = TextField('Enter Patient ID:', validators=[validators.required(), validators.Length(min=3, max=35)])

class registerForm(Form):
    """This form is for patient registration."""

    patientTitle = TextField('patientTitle:', validators=[validators.required()])
    patientFN = TextField('patientFN:', validators=[validators.required()])
    phone_number = TextField('phone_number:', validators=[validators.required()])
    patientID = TextField('patientID:', validators=[validators.required()])