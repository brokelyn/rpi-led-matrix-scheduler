import time
from rgbmatrix import graphics
import settings


class BootService:

    def __init__(self):
        self.add_fnc = None
        self.rmv_fnc = None
        self.fnc_id = None

    def init(self, add_loop, rmv_loop):
        self.add_fnc = add_loop
        self.rmv_fnc = rmv_loop

    def service(self, add_event):
        pass
