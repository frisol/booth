import os

path='./temp2/'

if not os.path.exists(path):
    os.makedirs(path)
    print ("Directory created")
else:
    print ("Directory already exists")