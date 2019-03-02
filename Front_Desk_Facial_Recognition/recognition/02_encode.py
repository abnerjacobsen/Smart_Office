# USAGE
# With default parameters
# 		python3 02_encode.py
# OR specifying the dataset, encodings and detection method
# 		python3 02_encode.py -i dataset -e encodings.pickle -d cnn

## Acknowledgement
## This code is adapted from:
## https://www.pyimagesearch.com/2018/06/18/face-recognition-with-opencv-python-and-deep-learning/

# import the necessary packages
from imutils import paths
import face_recognition
import argparse
import pickle
import cv2
import os

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--dataset", default='dataset',
	help="path to input directory of faces + images")
ap.add_argument("-e", "--encodings", default='encodings.pickle',
	help="path to serialized db of facial encodings")
ap.add_argument("-d", "--detection-method", type=str, default="hog",
	help="face detection model to use: either `hog` or `cnn`")
args = vars(ap.parse_args())

# grab the paths to the input images in our dataset
print("[INFO] quantifying faces...")
imagePaths = list(paths.list_images(args["dataset"]))

# initialize the list of known encodings and known names
knownEncodings = []
knownNames = []

# loop over the image paths
for (i, imagePath) in enumerate(imagePaths):
	# extract the person name from the image path
	print("[INFO] processing image {}/{}".format(i + 1,
		len(imagePaths)))
	name = imagePath.split(os.path.sep)[-2]

	# load the input image and convert it from RGB (OpenCV ordering)
	# to dlib ordering (RGB)
	image = cv2.imread(imagePath)
	rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

	# detect the (x, y)-coordinates of the bounding boxes
	# corresponding to each face in the input image
	boxes = face_recognition.face_locations(rgb,
		model=args["detection_method"])


	#Need to utilise face_landmarks to detect and encode eyes and smiles I think?
	#I just ran out of time to do this, however I found a link here, which I feel would have lead me
	#to a solution: 
	#https://pypi.org/project/face_recognition/
	#and here, for sure! :
	#https://face-recognition.readthedocs.io/en/latest/face_recognition.html
	#
	#Basically we can use something like this to get the features of each face and get eg. eyes like features['eye'] to encode them.
	# for box in boxes:
	# 	features = face_recognition.face_landmarks(box, face_locations=None, model='small') #to get a list of facial features
	#
	#This is where I got stuck, I couldn't find any reference to how to encode specific features and them append them to the encoding.
	#I feel there is a simple and straight forward way to do this, as we now have the feature, we just need to encode and append it?
	#


	# compute the facial embedding for the face
	encodings = face_recognition.face_encodings(rgb, boxes)

	# loop over the encodings
	for encoding in encodings:
		# add each encoding + name to our set of known names and
		# encodings
		knownEncodings.append(encoding)
		knownNames.append(name)

# dump the facial encodings + names to disk
print("[INFO] serializing encodings...")
data = {"encodings": knownEncodings, "names": knownNames}
f = open(args["encodings"], "wb")
f.write(pickle.dumps(data))
f.close()