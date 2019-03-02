"""These are the form validations used for Clerks webserver."""

from wtforms import TextField, validators, SelectField, BooleanField, Form

class addDocForm(Form):
    """This is form validation for adding a doctor."""
    
    doctorID = TextField('doctorID:', validators=[validators.required(), validators.Length(min=6, max=6)])
    doctorTitle = TextField('doctorTitle:', validators=[validators.required(), validators.Length(min=2, max=6)])
    doctorFN = TextField('doctorFN:', validators=[validators.required(), validators.Length(min=0, max=100)])
    phone_number = TextField('phone_number:', validators=[validators.required(), validators.Length(min=6, max=50)])
    specialty = TextField('specialty:', validators=[validators.required(), validators.Length(min=0, max=25)])
    regular_room = TextField('regular_room:', validators=[validators.required(), validators.Length(min=0, max=3)])

class BookApptForm1(Form):
    """This is form validation for preparing data for booking an appointment."""
    
    pid = TextField('Enter Patient ID:', validators=[validators.required(), validators.Length(min=6, max=6)])
    doctor = SelectField('Please select which doctor you wish to see:', validators=[validators.required(), validators.Length(min=0, max=30)])
    date = SelectField('Please select a date:', validators=[validators.required(), validators.Length(min=0, max=30)])

class BookApptForm2(Form):
    """This is form validation for actually booking the appointment."""
    
    pidTwo = TextField('Your ID: ', validators=[validators.required(), validators.Length(min=6, max=6)])
    doctorToSee = SelectField('Appointments for: ', validators=[validators.required(), validators.Length(min=0, max=100)])
    desiredDate = SelectField('on date: ', validators=[validators.required(), validators.Length(min=0, max=30)])
    time = SelectField('Available times:', validators=[validators.required(), validators.Length(min=4, max=10)])

class CancelApptForm(Form):
    """This is form validation for cancelling an appointment."""
    
    pid = TextField('Enter Patient ID:', validators=[validators.required(), validators.Length(min=6, max=6)])

class rmDocForm(Form):
    """This is form validation for removing a doctor."""
    
    doctorName = TextField('doctor_name:', validators=[validators.required(), validators.Length(min=0, max=100)])

class VPSForm(Form):
    """This is form validation for viewing patients seen for doctors."""
    
    doctor = TextField('doctor:', validators=[validators.required(), validators.Length(min=0, max=100)])
    startDate = TextField('startDate:', validators=[validators.required(), validators.Length(min=0, max=30)])
    endDate = TextField('endDate:', validators=[validators.required(), validators.Length(min=0, max=30)])
    week = BooleanField('week:', validators=[validators.required()])
    week = BooleanField('month:', validators=[validators.required()])