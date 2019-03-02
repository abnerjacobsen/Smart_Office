"""This module provides functions to intereact with the google calendar"""

from __future__ import print_function
import datetime
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import dateutil.parser
import json
import time


SCOPES = 'https://www.googleapis.com/auth/calendar'

#Get google authentication credentials
#Visual Studio Code
try:
    store = file.Storage('Assignment_Two/API/Library/googleCalendar/token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('Assignment_Two/API/Library/googleCalendar/credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))
except Exception as e:	
    #Pi Linux
    try:
        store = file.Storage('/home/pi/Assignment_Two/API/Library/googleCalendar/token.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('/home/pi/Assignment_Two/API/Library/googleCalendar/credentials.json', SCOPES)
            creds = tools.run_flow(flow, store)
        service = build('calendar', 'v3', http=creds.authorize(Http()))
    except Exception as e:
        #Windows Command Line
        try:
            store = file.Storage('token.json')
            creds = store.get()
            if not creds or creds.invalid:
                flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
                creds = tools.run_flow(flow, store)
            service = build('calendar', 'v3', http=creds.authorize(Http()))
        except Exception:
            print("Could not acquire credentials for Cal.")


def addToCalendar(name, location, description, dateOnly, start_time, end_time):
    """This function add's an event to the calendar. Specifially availability for a doctor"""

    startTime = "T" + str(start_time).strip() + ":00+11:00"
    endTime = "T" + str(end_time).strip() + ":00+11:00"

    timezone = 'Australia/Melbourne'

    time_start = str(dateOnly+startTime)
    time_end = str(dateOnly+endTime)

    event = {
        'summary': name,
        'location': location,
        'description': description,
        'start': {'dateTime': time_start,'timeZone': timezone},
        'end': {'dateTime': time_end,'timeZone': timezone}
        }
    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        return {"Code" : 200, "Message" : "Event created for '" + name + "' on: " + dateOnly + " [from: " + start_time + " to " + end_time + "]"}
    except Exception as e:
        return {"Code" : 400, "Message" : "Failed to create event! Reason: " + str(e)}

def getCalendarEvents(name, start_time, end_time, increment):
    """This function gets the events present between a start and end date"""

    timeArr = []

    utc_offset = ((time.localtime().tm_gmtoff)/3600)

    #utc_offset_hour
    uoh = int(utc_offset)
    #utc_offset_minutes
    uom = "{0:0=2d}".format(int(abs(utc_offset - uoh)*60))

    if utc_offset > 0:
        offset = "+"+str(uoh)+":"+str(uom)
    else:
        offset = "-"+str(uoh)+":"+str(uom)

    start = start_time.isoformat('T')+offset
    end = end_time.isoformat('T')+offset

    #List events from calendar with param's
    events_result = service.events().list(calendarId='primary', timeMin=start, 
                                            timeMax=end, singleEvents=True,
                                            orderBy='startTime'
                                            ).execute()

    #this is the list of events
    events = events_result.get('items', [])

    #if events defined (has elements), create a 
    #list of times from the start to the end time, 
    #following the increment provided
    if events:
        for event in events:
            try:
                summary = event['summary']
            except:
                summary = "No Summary"

            newName1temp = name.replace(".", " ")
            newName1 = newName1temp.replace(" ", "")

            newName2temp = summary.replace(".", " ")
            newName2 = newName2temp.replace(" ", "")

            if newName1 == newName2:
                startEvent = dateutil.parser.parse(event['start'].get('dateTime', event['start'].get('date')))
                endEvent = dateutil.parser.parse(event['end'].get('dateTime', event['end'].get('date')))

                print(startEvent, endEvent, summary)

                #datetime object of user search start time
                if dateutil.parser.parse(start) < startEvent:
                    startFrom = startEvent
                else:
                    startFrom = dateutil.parser.parse(start)
                print(startFrom)

                dividend = startFrom.time().minute
                divisor = increment
                quotient = dividend/divisor

                startMin = int(quotient) * divisor

                startFrom = startFrom.replace(minute=startMin, second=0, microsecond=0)

                if startFrom < startEvent:
                    startFrom += datetime.timedelta(minutes=increment)

                while startFrom < endEvent:
                    if (str(startFrom) not in timeArr):
                        timeArr.append(str(startFrom.time()))
                    startFrom += datetime.timedelta(minutes=increment)
            else:
                pass
    else:
        pass
    return json.dumps(timeArr)