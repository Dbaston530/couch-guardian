#  MBTechWorks.com 2016
#  Pulse Width Modulation (PWM) demo to cycle brightness of an LED

import RPi.GPIO as GPIO   # Import the GPIO library.
import time               # Import time library
import random
from pygame import mixer

class Deterrent:
    def __init__(self,audioFile):
        # Initialize mixer
        mixer.init()
        mixer.music.load(audioFile)
        self.rnum=random.Random()
        self.rnum.seed()
        
    def stop(self):
        mixer.music.stop()
        
    def activate(self, petType):     
        if petType == 1:
            mixer.music.stop()
            self.playNoise()
        else:
            mixer.music.play()

    def playNoise(self):
        GPIO.setmode(GPIO.BCM)  # choose BCM or BOARD numbering schemes. I use BCM  
        GPIO.setwarnings(False)
        GPIO.setup(40, GPIO.OUT)# set GPIO 25 as an output. You can use any GPIO port  
        p = GPIO.PWM(40, 50)    # create an object p for PWM on port 25 at 50 Hertz  
        p.start(70)             # start the PWM on 70 percent duty cycle  
        for x in range(1, 200):
            p.ChangeFrequency(self.rnum.randint(200,5000))  # change the frequency to x Hz (
            time.sleep(0.01*self.rnum.random())
        p.stop()                # stop the PWM output  
        #GPIO.cleanup()          # when your program exits, tidy up after yourself
