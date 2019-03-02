# PIoT_2018_Sem2_A2
Smart Office

===========================


**            **IMPORTANT!**            **
__!!! MUST READ CONFIGURATION SECTION !!!__

===========================

_________________________________________________________________________________
## --WHAT IS SMART OFFICE?--

This Smart Office IOT Solution is designed to automate a clinic environment.
See below to see what each user can do:

### --Patients--

__*Using the web interface:*__
    -Patients can register themselves online.
    -Patients can make an appointment to see a doctor.
    -Patients can cancel an appointment.
    -Patients can see announcments on their home page (Feature to be
        to be developed fully, **currently it is only a placeholder**)

__*Using the reception Google Assistant and Facial Recognition service:*__
    -Patients can make known their arrival via the facial recognition feature
        at the front desk by saying something like:

            >"Here for appointment"
                or
            >"Here for my appointment"
                or
            >"Here to see doctor <doctor name>"

    -Indirectly patients benefit from the Doctor Assistant feature 
        where they are called in the moment the doctor asks the 
        system to see them via the Waiting Room AI comm's system.

### --Clerks--

__*Using the web interface:*__
    -Clerks can make an appointment for a patient to see a doctor.
    -Clerks can cancel an appointment for a patient.
    -Clerks can view patients seen for a given period for all doctors.
        They can visualise the stats with a provided graph and tables.
    -Clerks can remove a doctor from the system (Additional Feature).
    -Clerks can add a doctor to the system (Additional Feature).
    -Clerks can view all current doctors in the system (Additional Feature).
    -Clerks can see announcments on their home page (Feature to be
        to be developed fully, **currently it is only a placeholder**)

### --Practitioners--

__*Using the web interface:*__
    -Practitioners can view patients records.
    -Practitioners can add notes to patients records via:
        **typing or dictating through speech**.
    -Practitioners can add a diagnosis to patients records via:
        **typing or dictating through speech**.
    -Practitioners can submit their availability to the clinics
        Google Calendar for a day or range of days/times.
    -Practitioners can see announcments on their home page (Feature
        to be developed fully, **currently it is only a placeholder**)

__*Using the Google Assistant:*__
    -Practitioners can ask for the information of their next appointment
        by saying:

            >"OK Google, next info"

        The Google Assistant AI will reply to them via voice with the 
        information of the next appointment without further actioning
        anything.

    -Practitioners can ask to call in the next patient quickly by saying:

            >"OK Google, next quick"
        
        The Google Assistant AI will reply to them via voice with the 
        information of the next appointment and also via Remote Procedure
        Call call in the next patient through the reception Pi. This feature
        is a less conversational version of calling in the next patient.

    -Practitioners can ask to call in the next patient normally by saying:

            >"OK Google, next patient"
        
        The Google Assistant AI will reply to them in a more natural 
        conversational way via voice with the information of the next 
        appointment and also via Remote Procedure Call call in the next
        patient through the reception Pi.
        
    -Practitioners can ask to remove last seen patient from waiting room
    list by saying:

            >"OK Google, done"
        
        The Google Assistant AI will reply by confirming the removal of the
        patient from the waiting room.

_________________________________________________________________________________
## --REQUIREMENTS--

### --Hardware--
    - 2 Raspberry Pi's model 2/3 (3 preffered).
    - a webcam for the reception pi (with inbuilt mic).
    - a microphone for the Doctor Assistant Pi.
    - Both Pi's must be able to connect to the internet or local network.
    __Optional__
        -Keyboards and HDMI enabled monitors for accessing the pi's.

### --Software--

#### --Required Modules/Libraries--
    -Open CV for reception pi (we have used the latest release 4.0.0-alpha).
    -You will need to make sure your audio configurations are correct.
    -You will also need Google Assistant installed onto your Pi.

    >>>There are plenty of online guides to perform the above tasks<<<

    -The following modules are to be installed on each pi
    (if not already present):

    (A great how to help guide is https://pypi.org/
    just simply type the name of the module/library in the search
    bar, and it will tell you what command to run on your Pi.)

        -Flask
        -Flask-SQLAlchemy
        -Flask-WTF
        -imagesize
        -Jinja2
        -requests
        -Sphinx
        -SQLAlchemy
        -flask-marshmallow
        -Flask-RESTful
        -Flask-Cors
        -dateutil.parser
        -datetime
        -pathlib
        -random
        -socket
        -time
        -json
        -os
        -googleapiclient.discovery
        -httplib2
        -oauth2client
        -wtforms
        -sqlite3
        -urllib
        -functools
        -pygal
        -logging
        -platform
        -re
        -sys
        -google.assistant.library.event
        -aiy
        -recognition.recognise
        -argparse
        -cv2
        -sense_hat
        -imutils
        -face_recognition
        -pickle
        -pico2wave

_________________________________________________________________________________
## --CONFIGURATION--            !!! -- MUST READ -- !!!

Inside API, Front_Desk_Facial_Recognition and WaitingRoomAPI directories, there
are config.json files. These files shoule **NEVER** be changed or altered unless
advised to by your IOT solutions specialists. These files contain information to 
connect your system to the cloud. Your IT specialist will be managing this cloud
service.

Inside the main directory (Assignment_Two), there is a config.json file. For now,
This will need to be updated each time an API has it's ip address changed. This
is the only way the webservers will be aware of the correct ip to send requests 
to for communicating with the API's.

_________________________________________________________________________________
## --MY PROJECT FILES--

Please note, there are files that had come with Assistant installs...etc.

To make it easier for the marker to determine my files to mark, I have listed
below the file/directory paths:

- All of API directory.
- All of Clerk directory.
- All of Patient directory.
- All of Practitioner directory.
- All of WaitingRoomAPI directory.
- All of Sphinx_Documentation  directory.
- All of Front_Desk_Facial_Recognition directory.
- Doctor_Assistant_1/src/AssistantPiConvo.py <<This is all I had modified in this directory>>
- Doctor_Assistant_1/src/AssistantPi.py <<This is NOT what I demonstrated. This was just a backup Assistant>>
- Front_Desk_Assistant/src/AssistantPi.py <<This is all I had modified in this directory>>

_________________________________________________________________________________
## --AUTHOR--

Savas Semirli
s3285220

_________________________________________________________________________________
## --AKNOWLEDGEMENTS--

Many thanks to the _Programming Internet Of Things_ teaching staff at RMIT University 
(Melbourne City Campus) 2018 Semester 2:

    -Shekhar Kalra ---------(Course Coordinator and Lecturer)
    -Kevin Ong -------------(Head Tutor)
    -Rodney Cocker ---------(Tutor and Lab Assistant)
    -Julien De-Sainte-Croix-(Tutor and Lab Assistant)
    -Tyrel Cameron ---------(Tutor and Lab Assistant)

They were a great supportive group, and inspried me to reach for new heights and 
create goals which I could only have dreamt of until having completed this course.

                    THANK YOU! :)

