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


# Set up GPIO mode
GPIO.setmode(GPIO.BCM)

# Clean up GPIO settings
GPIO.cleanup()