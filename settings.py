import os
from pathlib import Path

_BASE_PATH = Path(__file__).resolve().parent

# modules concatenate file names onto these, so keep the trailing separator
FONT_PATH = str(_BASE_PATH / 'fonts') + os.sep
IMAGES_PATH = str(_BASE_PATH / 'images') + os.sep

# modules.conf lives next to the code; the scheduler keeps it complete
# and the web interface edits it
MODULES_CONF = str(_BASE_PATH / 'modules.conf')
WEB_UI_PORT = int(os.environ.get('LEDSTATION_WEB_PORT', '8080'))

# Runtime Vars
LOADED_MODULES = 0
RUNNING_SERVICES = 0

############################### Constants
PATH_PYTHON_BINDING = '/home/pi/rpi-rgb-led-matrix/bindings/python'

# Unset variables stay None; a module that needs one will fail to initialise
# and gets skipped by the scheduler instead of crashing the whole application.

# Standby Service Module
STANDBY_DEVICE_IP = os.environ.get('STANDBY_DEVICE_IP')

# Pi Hole Module
PI_HOLE_IP = os.environ.get('PI_HOLE_IP')

# Syncthing Module
SYNCTHING_IP = os.environ.get('SYNCTHING_IP')
SYNCTHING_API_KEY = os.environ.get('SYNCTHING_API_KEY')
