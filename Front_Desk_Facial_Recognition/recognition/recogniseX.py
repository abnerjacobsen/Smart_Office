# USAGE
# With default parameters
#     python3 03_recognise.py
# OR specifying the encodings, screen resolution, output video and display
#     python3 03_recognise.py -e encodings.pickle -r 240 -o output/capture.avi -y 1

## Acknowledgement
## This code is adapted from:
## https://www.pyimagesearch.com/2018/06/18/face-recognition-with-opencv-python-and-deep-learning/

"""This module is used to encode images into an encodings.pickle file for face recognition to reference from"""

# import the necessary packages
from imutils.video import VideoStream
import face_recognition
from sense_hat import SenseHat
import argparse
import imutils
import pickle
import time
import cv2

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-e", "--encodings", default='/home/pi/Assignment_Two/Front_Desk_Facial_Recognition/recognition/encodings.pickle',
        help="path to serialized db of facial encodings")
ap.add_argument("-r", "--resolution", type=int, default=240,
        help="Resolution of the video feed")
ap.add_argument("-o", "--output", type=str,
        help="path to output video")
ap.add_argument("-y", "--display", type=int, default=0,
        help="whether or not to display output frame to screen")
ap.add_argument("-d", "--detection-method", type=str, default="hog",
        help="face detection model to use: either `hog` or `cnn`")
args = vars(ap.parse_args())

#prepare sensehat and sensehat data
SenseHat = SenseHat()

g1 = [0, 150, 0]
g2 = [0, 255, 0]
r = [255, 0, 0]
o = [0, 0, 0]

loading = [
        g1, g1, g1, g1, g1, g1, g1, g1,
        g1, g1, g1, g1, g1, g1, g1, g1,
        g1, g1, g1, g1, g1, g1, g1, g1,
        g1, g1, g1, g1, g1, g1, g1, g1,
        g1, g1, g1, g1, g1, g1, g1, g1,
        g1, g1, g1, g1, g1, g1, g1, g1,
        g1, g1, g1, g1, g1, g1, g1, g1,
        g1, g1, g1, g1, g1, g1, g1, g1
]

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

failed = [
        o, r, r, r, r, r, o, o,
        o, r, r, r, r, r, o, o,
        o, r, r, o, o, o, o, o,
        o, r, r, r, r, o, o, o,
        o, r, r, r, r, o, o, o,
        o, r, r, o, o, o, o, o,
        o, r, r, o, o, o, o, o,
        o, r, r, o, o, o, o, o,
]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def recognise():
        """This function is responsible for using the camera to recognise the
        person standing infront of the device. Returns the recognised persons
        name."""

        #keep track of attempts. Too many attempts will trigger a return.
        attempts = 0
        # load the known faces and embeddings
        print("[INFO] loading encodings...")
        data = pickle.loads(open(args["encodings"], "rb").read())

        # initialize the video stream and pointer to output video file, then
        # allow the camera sensor to warm up
        #Using a for loop to loop through devices, as a precaution to 
        #system related issues, whereby a resource might be allocated a different
        #device number for various reasons.
        print("[INFO] starting video stream...")
        for x in range(0, 11):
           vs = VideoStream(src=x).start()
           if str(vs.read()) != "None":
              break
        writer = None

        #Faint green to indicate starting process
        SenseHat.set_pixels(loading)
        time.sleep(2.0)

        # loop over frames from the video file stream
        while True:
           SenseHat.set_pixels(working)
           if attempts >35:
              SenseHat.set_pixels(failed)
              time.sleep(1.5)
              SenseHat.clear()
              cv2.destroyAllWindows()
              vs.stop()
              return {'code' : 400}
           attempts += 1
            # grab the frame from the threaded video stream
           frame = vs.read()

           # convert the input frame from BGR to RGB then resize it to have
           # a width of 750px (to speedup processing)
           rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
           rgb = imutils.resize(frame, width=args["resolution"])
           r = frame.shape[1] / float(rgb.shape[1])

           # detect the (x, y)-coordinates of the bounding boxes
           # corresponding to each face in the input frame, then compute
           # the facial embeddings for each face
           boxes = face_recognition.face_locations(rgb,
                   model=args["detection_method"])
           encodings = face_recognition.face_encodings(rgb, boxes)
           names = []

           # loop over the facial embeddings
           for encoding in encodings:
               # attempt to match each face in the input image to our known
              # encodings
              matches = face_recognition.compare_faces(data["encodings"],
                      encoding)
              name = "Unknown"

              # check to see if we have found a match
              if True in matches:
                  # find the indexes of all matched faces then initialize a
                 # dictionary to count the total number of times each face
                 # was matched
                 matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                 counts = {}

                 # loop over the matched indexes and maintain a count for
                 # each recognized face face
                 for i in matchedIdxs:

                #     name = data["names"][i].split("-")[0].replace("_", " ")
                    name = data["names"][i]
                    counts[name] = counts.get(name, 0) + 1

                 # determine the recognized face with the largest number
                 # of votes (note: in the event of an unlikely tie Python
                 # will select first entry in the dictionary)
                 name = max(counts, key=counts.get)

              # update the list of names
              names.append(name)

           # loop over the recognized faces
           for ((top, right, bottom, left), name) in zip(boxes, names):
               # rescale the face coordinates
              top = int(top * r)
              right = int(right * r)
              bottom = int(bottom * r)
              left = int(left * r)
      
              # print to console, identified person
              personFound = 'Person found: {}'.format(name)
              print(personFound) 
              cv2.destroyAllWindows()
              vs.stop()

              # check to see if the video writer point needs to be released
              if writer is not None:
                 writer.release()
              SenseHat.clear()
              cv2.destroyAllWindows()
              vs.stop()
              return {'code' : 200, 'identified' : name}

           # if the video writer is None *AND* we are supposed to write
           # the output video to disk initialize the writer
           if writer is None and args["output"] is not None:
              fourcc = cv2.VideoWriter_fourcc(*"MJPG")
              writer = cv2.VideoWriter(args["output"], fourcc, 20, (frame.shape[1], frame.shape[0]), True)

           # if the writer is not None, write the frame with recognized
           # faces to disk
           if writer is not None:
               writer.write(frame)

           # check to see if we are supposed to display the output frame to
           # the screen
           if args["display"] > 0:
              cv2.imshow("Frame", frame)
              key = cv2.waitKey(1) & 0xFF

              # if the `q` key was pressed, break from the loop
              if key == ord("q"):
                  break

        # do a bit of cleanup
        cv2.destroyAllWindows()
        vs.stop()

        # check to see if the video writer point needs to be released
        if writer is not None:
            writer.release()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Run Program
if __name__ == '__main__':
        recognise()