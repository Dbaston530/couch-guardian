'''
Couch-Guard ver.3: removing OpenCV window visualization operations to increase speed
    -added LED and sound functionality

***To install IBM Watson IoT Platform:
sudo apt-get update
sudo apt-get install python-dev python-pip
sudo pip3 install wiotp-sdk psutil
wget https://github.com/ibm-watson-iot/iot-python/archive/master.zip
unzip master.zip
cd iot-python-master/samples/psutil/src

***To test IBM Watson IoT connections:
python3 iotpsutil.py --quickstart

***To install Cloudant:
pip3 install cloudant

***To install Bson and Pmongo (to serialize datetime):
pip3 install bson
pip3 install pymongo

***To install PIL (for motion detection with picam):
sudo apt-get install python-imaging-tk

***To install pygame:
(check online if not already installed)

***Dependencies for tensorflow-lite
***Packages for Open CV
sudo apt-get -y install libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev
sudo apt-get -y install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt-get -y install libxvidcore-dev libx264-dev
sudo apt-get -y install qt4-dev-tools libatlas-base-dev

pip3 install opencv-python==3.4.6.27

***Packages for Tensorflow
pip3 install tensorflow

version=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')

if [ $version == "3.7" ]; then
wget https://github.com/lhelontra/tensorflow-on-arm/releases/download/v2.0.0/tensorflow-2.0.0-cp37-none-linux_armv7l.whl
pip3 install tensorflow-2.0.0-cp37-none-linux_armv7l.whl
rm tensorflow-2.0.0-cp37-none-linux_armv7l.whl
fi

if [ $version == "3.5" ]; then
wget https://github.com/lhelontra/tensorflow-on-arm/releases/download/v1.14.0/tensorflow-1.14.0-cp35-none-linux_armv7l.whl
pip3 install tensorflow-1.14.0-cp35-none-linux_armv7l.whl
rm tensorflow-1.14.0-cp35-none-linux_armv7l.whl
fi

'''

#from gpiozero import LED, Button
import RPi.GPIO as GPIO
from picamera import PiCamera
from time import sleep
import random
from pygame import mixer
import threading
#from pkg.credentials import *
from pkg.IBMWatsonIoT import *
from pkg.IBMDatabase import *
#from pkg.picamMotionDetect import *
from pkg.petDetection import *

# Image recog imports added by D.B.
# Import packages
import os
import argparse
import cv2
import numpy as np
import sys
import glob
import time
import importlib.util
from threading import Thread

# If tensorflow is not installed, import interpreter from tflite_runtime, else import from regular tensorflow
pkg = importlib.util.find_spec('tensorflow')
if pkg is None:
    from tflite_runtime.interpreter import Interpreter
else:
    from tensorflow.lite.python.interpreter import Interpreter

# Function wrapper to run data upload to cloud in separate thread
def uploadWrapper (db):
    db.addData(msg)
    sendSignalToWatsonIoT(orgId,typeId,deviceId,token,msg[1])


'''
camera = PiCamera()
camera.rotation = 180
camera.start_preview()
for effect in camera.IMAGE_EFFECTS:
    camera.image_effect = effect
    sleep(3)
    camera.capture('/home/pi/CouchG/testpy_%s.jpg' % effect)
camera.stop_preview()
'''

# Define VideoStream class to handle streaming of video from webcam in separate processing thread
# Source - Adrian Rosebrock, PyImageSearch: https://www.pyimagesearch.com/2015/12/28/increasing-raspberry-pi-fps-with-python-and-opencv/
class VideoStream:
    """Camera object that controls video streaming from the Picamera"""
    def __init__(self,resolution=(640,480),framerate=30):
        # Initialize the PiCamera and the camera image stream
        self.stream = cv2.VideoCapture(0)
        ret = self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        ret = self.stream.set(3,resolution[0])
        ret = self.stream.set(4,resolution[1])
            
        # Read first frame from the stream
        (self.grabbed, self.frame) = self.stream.read()

    # Variable to control when the camera is stopped
        self.stopped = False

    def start(self):
    # Start the thread that reads frames from the video stream
        Thread(target=self.update,args=()).start()
        return self

    def update(self):
        # Keep looping indefinitely until the thread is stopped
        while True:
            # If the camera is stopped, stop the thread
            if self.stopped:
                # Close camera resources
                self.stream.release()
                return

            # Otherwise, grab the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
    # Return the most recent frame
        return self.frame

    def stop(self):
    # Indicate that the camera and thread should be stopped
        self.stopped = True
        
# TFLite arguments
MODEL_NAME = "Sample_TFLite_model"
GRAPH_NAME = "detect.tflite"
LABELMAP_NAME = "labelmap.txt"
min_conf_threshold = 0.5

resW, resH = 1280, 720
imW, imH = int(resW), int(resH)

# Get path to current working directory
CWD_PATH = os.getcwd()

# Path to .tflite file, which contains the model that is used for object detection
PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,GRAPH_NAME)

# Path to label map file
PATH_TO_LABELS = os.path.join(CWD_PATH,MODEL_NAME,LABELMAP_NAME)

# Load the label map
with open(PATH_TO_LABELS, 'r') as f:
    labels = [line.strip() for line in f.readlines()]

# Have to do a weird fix for label map if using the COCO "starter model" from
# https://www.tensorflow.org/lite/models/object_detection/overview
# First label is '???', which has to be removed.
if labels[0] == '???':
    del(labels[0])

# Load the Tensorflow Lite model and get details
interpreter = Interpreter(model_path=PATH_TO_CKPT)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
height = input_details[0]['shape'][1]
width = input_details[0]['shape'][2]

floating_model = (input_details[0]['dtype'] == np.float32)

input_mean = 127.5
input_std = 127.5

# Initialize frame rate calculation
frame_rate_calc = 1
freq = cv2.getTickFrequency()

# Initialize video stream
videostream = VideoStream(resolution=(imW,imH),framerate=30).start()
time.sleep(1)

# IBM credentials
# Please see credentials.py


# IBM Watson credentials


# Global variable
isMotion=[False,'imagePath']

# Pi hardware initialization:
#button = Button(17)
#led = LED(21)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)

# mixer settings
audioFile = 'res/sample.mp3'

# General settings
lastClassifyTime = 0
lastActivatedTime = 0
lastUploadTime = 0
minWaitingTime = 10
minClassifyTime = 5

petClass = ['Non-Pet','Cat','Dog']
msg=['Yes',petClass[0]]

# IBM Cloudant config:
dbName= "cgdb"

#### Main code starts here ####

# Initialize mixer
mixer.init()
mixer.music.load(audioFile)

# IBM Cloudant connection
db=IBMDatabase(deviceID,username,apikey)
db.connect()
db.createDatabase(dbName)
db.disconnect()

# Start motion detection in new thread
#thrMotion=threading.Thread(target=detectMotion,args=(isMotion,))
#thrMotion.start()

# Seed random number
#random.seed()

while True:
    # Start timer (for calculating frame rate)
    #t1 = cv2.getTickCount()

    # Grab frame from video stream
    frame1 = videostream.read()

    # Acquire frame and resize to expected shape [1xHxWx3]
    frame = frame1.copy()
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_resized = cv2.resize(frame_rgb, (width, height))
    input_data = np.expand_dims(frame_resized, axis=0)

    # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
    if floating_model:
        input_data = (np.float32(input_data) - input_mean) / input_std

    # Perform the actual detection by running the model with the image as input
    interpreter.set_tensor(input_details[0]['index'],input_data)
    interpreter.invoke()

    # Retrieve detection results
    boxes = interpreter.get_tensor(output_details[0]['index'])[0] # Bounding box coordinates of detected objects
    classes = interpreter.get_tensor(output_details[1]['index'])[0] # Class index of detected objects
    scores = interpreter.get_tensor(output_details[2]['index'])[0] # Confidence of detected objects
    
    station_ymax = 0
    station_ymin = 0
    station_xmax = 0
    station_xmin = 0
    
    petType = petClass[0]
    
    pet_x = 0
    pet_y = 0
    
    pet_on_furniture = False
    
    ###
    # Loop over all detections and draw detection box if confidence is above minimum threshold
    for i in range(len(scores)):
        if ((scores[i] > min_conf_threshold) and (scores[i] <= 1.0)):

            # Get bounding box coordinates and draw box
            # Interpreter can return coordinates that are outside of image dimensions, need to force them to be within image using max() and min()
            ymin = int(max(1,(boxes[i][0] * imH)))
            xmin = int(max(1,(boxes[i][1] * imW)))
            ymax = int(min(imH,(boxes[i][2] * imH)))
            xmax = int(min(imW,(boxes[i][3] * imW)))
            
            #cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), (10, 255, 0), 2)

            # Draw label
            object_name = labels[int(classes[i])] # Look up object name from "labels" array using class index
            '''
            label = '%s: %d%%' % (object_name, int(scores[i]*100)) # Example: 'person: 72%'
            labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2) # Get font size
            label_ymin = max(ymin, labelSize[1] + 10) # Make sure not to draw label too close to top of window
            cv2.rectangle(frame, (xmin, label_ymin-labelSize[1]-10), (xmin+labelSize[0], label_ymin+baseLine-10), (255, 255, 255), cv2.FILLED) # Draw white box to put label text in
            cv2.putText(frame, label, (xmin, label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2) # Draw label text
            '''
            
            # Save bounding box info for pet 
            if (object_name == 'cat' or object_name == 'dog' or object_name == 'teddy bear'):
                if (object_name == 'cat'):
                    petType = 1
                else:
                    petType = 2
                pet_x = int((xmin + xmax) / 2)
                pet_y = int((ymin + ymax) / 2)
                # Draw a circle at center of pet
                #cv2.circle(frame,(pet_x,pet_y), 5, (75,13,180), -1)
                #pet_ymax = ymax
                #pet_ymin = ymin
                #pet_xmax = xmax
                #pet_xmin = xmin
                
            # Save bounding box info for furniture    
            elif (object_name == 'couch' or object_name == 'chair' or object_name == 'dining table'):
                station_ymax = int((ymin + ymax) / 2)
                station_ymin = ymin
                station_xmax = xmax
                station_xmin = xmin
    
    # Check if animal is on furniture
    if (pet_x < station_xmax and pet_x > station_xmin and pet_y < station_ymax and pet_y > station_ymin):
        pet_on_furniture = True
        #cv2.putText(frame,'Pet on Furniture!!!',(100,50),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,0),2,cv2.LINE_AA)
        #TODO:
        #finish labels for test frames with cv2 and test with teddy bear and chair
        #look up mechanic to output to node red
        #    with node red research reaction function for gpio
        #    log date and time to database for activation
        #    set sleep time for device action
        #    use node red to initiate a video save to database?
        #       or create video save file from here? (i think not, how would I save, send, then delete/clean files?
        #after testing, remove frame labels
    ###
    # Draw framerate in corner of frame
    #cv2.putText(frame,'FPS: {0:.2f}'.format(frame_rate_calc),(30,50),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,0),2,cv2.LINE_AA)

    # All the results have been drawn on the frame, so it's time to display it.
    cv2.imshow('Object detector', frame)

    # Calculate framerate
    #t2 = cv2.getTickCount()
    #time1 = (t2-t1)/freq
    #frame_rate_calc= 1/time1

    # Press 'q' to quit
    if cv2.waitKey(1) == ord('q'):
        break
    
    #if motion is detected:
    if (object_name == 'cat' or object_name == 'dog'):
        if (pet_on_furniture == True):
            GPIO.output(21, True)
        else:
            GPIO.output(21, False)
        
        print("pet detected")
        
        # if more than minClassifyTime beyond last pet classification time,
        # then classify and check for pet time
        if (time.time() - lastClassifyTime) > minClassifyTime:
            #imagePath = isMotion[1]
            #petType = classifyPet(imagePath)
            msg[1]=petClass[petType]
            lastClassifyTime = time.time()
    
        # if more than minWaitingTime beyond last activation,
        # then activate deterrent if pet is detected        
        if (time.time() - lastActivatedTime) > minWaitingTime:         
            if (petType > 0):
                mixer.music.play()            
                lastActivatedTime = time.time()
                
        # if more than minWaitingTime beyong last motion detection,
        # then upload data to IBM Cloudant and send signal to WatsonIoT
        # in new threads
        if (time.time() - lastUploadTime) > minWaitingTime:
            #thrUpload=threading.Thread(target=uploadWrapper,args=(db,))
            #thrUpload.start()
            lastUploadTime = time.time()    
    else:
        GPIO.output(21, False)
        # audio plays for at least minWaitingTime seconds
        if (time.time() - lastActivatedTime) > minWaitingTime:            
            mixer.music.stop()
# Clean up
cv2.destroyAllWindows()
videostream.stop()
