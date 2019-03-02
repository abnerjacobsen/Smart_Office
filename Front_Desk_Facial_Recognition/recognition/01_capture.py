
"""This module is used to capture image and recognise faces, eyes and smile within
said images. Also saves the images to file, naming the file the name provided on
executing of the script with argument -n "<Name>_<LastName>-<patientID>" 
(eg: Jerry_Lewis-222222) """

import argparse
import os
import time

import cv2
from sense_hat import SenseHat

#Prepare sensehat led data
sense = SenseHat()
g2 = [0, 255, 0]
working = [
        g2, g2, g2, g2, g2, g2, g2, g2,
        g2, g2, g2, g2, g2, g2, g2, g2,
        g2, g2, g2, g2, g2, g2, g2, g2,
        g2, g2, g2, g2, g2, g2, g2, g2,
        g2, g2, g2, g2, g2, g2, g2, g2,
        g2, g2, g2, g2, g2, g2, g2, g2,
        g2, g2, g2, g2, g2, g2, g2, g2,
        g2, g2, g2, g2, g2, g2, g2, g2
]

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-n", "--name", required=True,
    help="The name/id of this person you are recording")
ap.add_argument("-i", "--dataset", default='dataset',
    help="path to input directory of faces + images")
args = vars(ap.parse_args())

# use name as folder name
name = args["name"]
folder = './dataset/{}'.format(name)

# Create a new folder for the new name
if not os.path.exists(folder):
    os.makedirs(folder)

#prepare haarcascades
face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
eye_detector = cv2.CascadeClassifier('haarcascade_eye.xml')
smile_detector = cv2.CascadeClassifier('haarcascade_smile.xml')

#used to label the image file name
img_counter = 0

while True:
    #clear sensehat leds when running
    sense.clear()

    #Continue to take more images?
    key = input("Press q to quit or ENTER to continue to take more images: ")
    if key == 'q':
        break

    ret, frame = cv2.VideoCapture(0).read()
    if not ret:
        print("Camera returned False - No image supplied!")
        break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(70, 70),
    )
    #Draw rectangles around found features:
    #
    #face found!
    for (x,y,w,h) in faces:
        print("found a face")

        #Flash sensehat when face found!
        sense.set_pixels(working)
        time.sleep(0.25)
        cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0), 2)
        img_name = "{}/{:04}.jpg".format(folder,img_counter)
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = frame[y:y+h, x:x+w]
        
        eyes = eye_detector.detectMultiScale(
            roi_gray,
            scaleFactor= 1.3,
            minNeighbors=5,
            minSize=(15, 25),
            )
        
        #eye/s found!
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
               
        
        smile = smile_detector.detectMultiScale(
            roi_gray,
            scaleFactor= 1.1,
            minNeighbors=15,
            minSize=(15, 50),
            )

        #smile found!
        for (xx, yy, ww, hh) in smile:
            cv2.rectangle(roi_color, (xx, yy), (xx + ww, yy + hh), (0, 255, 0), 2)
        
        #save image to file
        cv2.imwrite(img_name, frame[y:y+h,x:x+w])
        print("{} written!".format(img_name))
        
    img_counter += 1

#close everything for clean up
cv2.VideoCapture(0).release()
cv2.destroyAllWindows()
