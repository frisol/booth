# Author: Ben Hasler
# Date: 14/10/2024
# Description: This script is used to control the photo booth. It will take photos and save them to a folder on the Raspberry Pi.

# Import the necessary libraries
# import RPi.GPIO as GPIO
import os
import glob
import time
import traceback
from time import sleep
import atexit
import sys
import socket
import pygame
import random
import config # this is the config python file config.py

# Set up GPIO mode
# GPIO.setmode(GPIO.BCM)

# Clean up GPIO settings
# GPIO.cleanup()

########################
### Variables Config ###
########################
led_pin = 7 # LED
flash_pin = 11  # Pin for the LED camera flash 
btn_pin = 18 # pin for the start button

total_pics = 4 # number of pics to be taken
capture_delay = 1 # delay between pics
prep_delay = 5 # number of seconds at step 1 as users prep to have photo taken
gif_delay = 100 # How much time between frames in the animated gif
restart_delay = 5 # how long to display finished message before beginning a new session

# full frame of v1 camera is 2592x1944. Wide screen max is 2592,1555
# if you run into resource issues, try smaller, like 1920x1152. 
# or increase memory http://picamera.readthedocs.io/en/release-1.12/fov.html#hardware-limits
high_res_w = 3280 # width of high res image, if taken
high_res_h = 2464 # height of high res image, if taken

#############################
### Variables that Change ###
#############################
# Do not change these variables, as the code will change it anyway
transform_x = config.monitor_w # how wide to scale the jpg when replaying
transfrom_y = config.monitor_h # how high to scale the jpg when replaying
offset_x = 0 # how far off to left corner to display photos
offset_y = 0 # how far off to left corner to display photos
replay_delay = 1 # how much to wait in-between showing pics on-screen after taking
replay_cycles = 1 # how many times to show each photo on-screen after taking

####################
### Other Config ###
####################
real_path = os.path.dirname(os.path.realpath(__file__))