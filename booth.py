# Author: Ben Hasler
# Date: 14/10/2024
# Description: This script is used to control the photo booth. It will take photos and save them to a folder on the Raspberry Pi.

# Import the necessary libraries
import RPi.GPIO as GPIO
from picamera2 import Picamera2

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
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)



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

#####################
# initialize pygame #
#####################
pygame.init()
pygame.display.set_mode((config.monitor_w, config.monitor_h))
screen = pygame.display.get_surface()
pygame.display.set_caption('Photo Booth Pics')
pygame.mouse.set_visible(False) #hide the mouse cursor
# pygame.display.toggle_fullscreen()

#################
### Functions ###
#################

# clean up running programs as needed when main program exits
def cleanup():
  print('Ended abruptly')
  pygame.quit()
  # GPIO.cleanup()
atexit.register(cleanup)

# A function to handle keyboard/mouse/device input events    
def input(events):
    for event in events:  # Hit the ESC key to quit the slideshow.
        if (event.type == QUIT or
            (event.type == KEYDOWN and event.key == K_ESCAPE)):
            pygame.quit()

#create folder
def create_pics_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print ("Directory created")
    else:
        print ("Directory already exists")

#delete files in folder
def clear_pics(channel):
	files = glob.glob(config.file_path + '*')
	for f in files:
		os.remove(f) 
	#light the lights in series to show completed
	print ("Deleted previous pics")
	for x in range(0, 3): #blink light
		GPIO.output(led_pin,True); 
		sleep(0.25)
		GPIO.output(led_pin,False);
		sleep(0.25)
          
# set variables to properly display the image on screen at right ratio
def set_demensions(img_w, img_h):
	# Note this only works when in booting in desktop mode. 
	# When running in terminal, the size is not correct (it displays small). Why?

    # connect to global vars
    global transform_y, transform_x, offset_y, offset_x

    # based on output screen resolution, calculate how to display
    ratio_h = (config.monitor_w * img_h) / img_w 

    if (ratio_h < config.monitor_h):
        #Use horizontal black bars
        #print "horizontal black bars"
        transform_y = ratio_h
        transform_x = config.monitor_w
        offset_y = (config.monitor_h - ratio_h) / 2
        offset_x = 0
    elif (ratio_h > config.monitor_h):
        #Use vertical black bars
        #print "vertical black bars"
        transform_x = (config.monitor_h * img_w) / img_h
        transform_y = config.monitor_h
        offset_x = (config.monitor_w - transform_x) / 2
        offset_y = 0
    else:
        #No need for black bars as photo ratio equals screen ratio
        #print "no black bars"
        transform_x = config.monitor_w
        transform_y = config.monitor_h
        offset_y = offset_x = 0

    # uncomment these lines to troubleshoot screen ratios
#     print str(img_w) + " x " + str(img_h)
#     print "ratio_h: "+ str(ratio_h)
#     print "transform_x: "+ str(transform_x)
#     print "transform_y: "+ str(transform_y)
#     print "offset_y: "+ str(offset_y)
#     print "offset_x: "+ str(offset_x)

# display one image on screen
def show_image(image_path, angle, img_size):

	# clear the screen
	screen.fill( (0,0,0) )

	# load the image
	img = pygame.image.load(image_path)
	img = img.convert() 

	# set pixel dimensions based on image
	set_demensions(img.get_width(), img.get_height())

	# rescale the image to fit the current display
	img = pygame.transform.scale(img, (int(transform_x), int(transfrom_y)))
	img = pygame.transform.rotate(img, angle)
	screen.blit(img,(offset_x + img_size, offset_y + img_size))
	pygame.display.flip()

# display a blank screen
def clear_screen():
	screen.fill( (0,0,0) )
	pygame.display.flip()
     
# display a group of images
def display_pics(jpg_group, rotate, img_scale):
	for i in range(0, replay_cycles): #show pics a few times
		for i in range(1, total_pics+1): #show each pic
			show_image(config.file_path + jpg_group + "-0" + str(i) + ".jpg", rotate * random.randint(-5,5), img_scale)
			time.sleep(replay_delay) # pause
                  
# define the photo taking function for when the big button is pressed 
def start_photobooth(): 

    create_pics_folder(config.file_path)
    create_pics_folder(config.display_path)
    create_pics_folder(config.pose_path)

    input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.

	################################# Begin Step 1 #################################
	
    print ("Get Ready")
    GPIO.output(led_pin,False);
	## show_image(real_path + "/instructions.png")
    show_image(config.pose_path + random.choice(os.listdir(config.pose_path)), 0, 0)
    sleep(prep_delay)
	
	# clear the screen
    clear_screen()
    camera = PiCamera2()
    camera.vflip = False
    camera.hflip = True # flip for preview, showing users a mirror image
	# camera.saturation = -100 # comment out this line if you want color images
    camera.iso = config.camera_iso
	
    pixel_width = 0 # local variable declaration
    pixel_height = 0 # local variable declaration
	
    if config.hi_res_pics:
        camera.resolution = (high_res_w, high_res_h) # set camera resolution to high res
    else:
        pixel_width = 500 # maximum width of animated gif on tumblr
        pixel_height = config.monitor_h * pixel_width // config.monitor_w
        camera.resolution = (pixel_width, pixel_height) # set camera resolution to low res

################################# Begin Step 2 #################################
    
    print ("Taking pics")

    now = time.strftime("%Y-%m-%d-%H-%M-%S") #get the current date and time for the start of the filename
	
    if config.capture_count_pics:
        try: # take the photos
            for i in range(1,total_pics+1):
                show_image(real_path + "/pose" + str(i) + ".jpg")
                time.sleep(capture_delay) # pause in-between shots
                clear_screen()
                camera.hflip = True # preview a mirror image
                if config.flash_enabled:
                    GPIO.output(flash_pin, True)
                    print("flash on")
                camera.start_preview(
				resolution=(config.monitor_w, config.monitor_h)) # start preview at low res but the right ratio
                time.sleep(2) #warm up camera
                GPIO.output(led_pin,True) #turn on the LED
                filename = config.file_path + now + '-0' + str(i) + '.jpg'
                camera.hflip = True # flip back when taking photo
                camera.capture(filename)
                GPIO.output(flash_pin, False)
                print(filename)
                GPIO.output(led_pin,False) #turn off the LED
                camera.stop_preview()
				# show_image(real_path + "/pose" + str(i) + ".jpg")
				# time.sleep(capture_delay) # pause in-between shots
				# clear_screen()
                if i == total_pics+1:
                    break
        finally:
            camera.close()
            # GPIO.output(flash_pin, False)
    else:
        camera.start_preview(
			resolution=(config.monitor_w, config.monitor_h)) # start preview at low res but the right ratio
        time.sleep(2) #warm up camera
		
        try: #take the photos
            for i, filename in enumerate(
					camera.capture_continuous(config.file_path + now + '-' + '{counter:02d}.jpg')):
                GPIO.output(led_pin,True) #turn on the LED
                print(filename)
                time.sleep(capture_delay) # pause in-between shots
                GPIO.output(led_pin,False) #turn off the LED
                if i == total_pics-1:
                    break
        finally:
            camera.stop_preview()
            camera.close()


########################### Begin Step 3 #################################

    input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.
	
    if config.post_online:
	    show_image(real_path + "/uploading.png")
    else:
	    show_image(real_path + "/processing.jpg")
         

####################
### Main Program ###
####################

## clear the previously stored pics based on config settings
if config.clear_on_startup:
	clear_pics(1)

print ("Photo booth app running...")
for x in range(0, 5): #blink light to show the app is running
    GPIO.setup(led_pin, GPIO.OUT)
    GPIO.output(led_pin,True)
    sleep(0.25)
    GPIO.output(led_pin,False)
    sleep(0.25)

## show_image(real_path + "/intro.png");
## show_image(real_path + "/pics/2020-06-27-21-54-27-01-blur+text.jpg");

while True:
	## show_image(config.display_path + "2020-06-27-22-17-02-01-blur+text.jpg");
	# show_image(config.display_path + random.choice(os.listdir(config.display_path)))
	## random_file=random.choice(os.listdir("Folder_Destination"))
	GPIO.output(led_pin,True); #turn on the light showing users they can push the button
	input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.
	GPIO.wait_for_edge(btn_pin, GPIO.FALLING)
	time.sleep(config.debounce) #debounce
	start_photobooth()
     
# Clean up GPIO settings
GPIO.cleanup()