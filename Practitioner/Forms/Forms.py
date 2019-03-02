"""This module contains all the forms for practitioners."""

from wtforms import validators, TextField, SelectField, Form

class DVPForm1(Form):
    """This is form validation for loading patient history."""
    
    pid = TextField('Enter Patient ID', validators=[validators.required(), validators.Length(min=6, max=6)])

class DVPForm2(Form):
    """This is form validation for submitting notes and diagnosis."""
    
    patientHistory = TextField('Patient History:', validators=[validators.required()])
    addNote = TextField('Add Note To Patient History:', validators=[validators.required()])
    addDiagnoses = TextField('Add Diagnoses To Patient History:', validators=[validators.required()])

class SAForm(Form):
    """This is form validation for doctors submition of availability."""
    
    doctor = SelectField('I am:', validators=[validators.required(), validators.Length(min=3, max=100)])
    startDate = SelectField('Start Date:', validators=[validators.required(), validators.Length(min=3, max=35)])
    endDate = SelectField('End Date:', validators=[validators.required(), validators.Length(min=3, max=35)])