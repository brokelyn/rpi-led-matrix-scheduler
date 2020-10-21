import os

dirname = os.path.abspath(__file__)
split = dirname.split('/')
filename = split[len(split) - 1]

# Constants
PATH_PYTHON_BINDING = '/home/pi/rpi-rgb-led-matrix/bindings/python'

FONT_PATH = dirname.replace(filename, 'fonts/')
IMAGES_PATH = dirname.replace(filename, 'images/')

STANDBY_DEVICE_IP = os.environ['STANDBY_DEVICE_IP']
PI_HOLE_IP = os.environ['PI_HOLE_IP']
SYNCTHING_IP = os.environ['SYNCTHING_IP']
SYNCTHING_API_KEY = os.environ['SYNCTHING_API_KEY']
SYNCTHING_FOLDER_ID = os.environ['SYNCTHING_FOLDER_ID']

# Runtime Vars
LOADED_MODULES = 0
RUNNING_SERVICES = 0

