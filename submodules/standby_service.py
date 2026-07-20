import time
from rgbmatrix import graphics
from submodule import Submodule, load_font
import ping3
import settings


class StandbyService(Submodule):

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)
        self.font = load_font("6x13B.bdf")
        self.online = True

    def ping(self, ip, n):
        counter = 0
        for i in range(n):
            try:
                result = ping3.ping(ip, unit="ms", timeout=5, size=2)
                if not result:  # inactive
                    counter += 1
                else:
                    return 0
            except:
                counter += 1
        return counter

    def service(self):
        time.sleep(60) # start detecting after timeout
        while True:
            if self.online:
                if self.fnc_id:
                    self.rmv_loop(self.fnc_id)
                    self.add_event(1, self.welcome)
                while True:
                    if self.ping(settings.STANDBY_DEVICE_IP, 5) == 5:
                        self.online = False
                        break
                    time.sleep(20)
            else:
                self.add_event(1, self.goodbye)
                self.fnc_id = self.add_loop(1, self.standby)
                while True:
                    if self.ping(settings.STANDBY_DEVICE_IP, 1) == 0:
                        self.online = True
                        break
                    time.sleep(25)

    def standby(self, matrix):
        swap = self.get_canvas(matrix)
        self.swap_canvas(matrix, swap)
        time.sleep(15)

    def welcome(self, matrix):
        swap = self.get_canvas(matrix)
        text_color = graphics.Color(170, 0, 170)

        graphics.DrawText(swap, self.font, 10, self.font.baseline - 2, text_color, "Welcome")
        graphics.DrawText(swap, self.font, 20, self.font.baseline + 8, text_color, "back")
        graphics.DrawText(swap, self.font, 2, self.font.baseline + 19, text_color, "Was sgdn?")

        self.swap_canvas(matrix, swap)
        time.sleep(5.5)

    def goodbye(self, matrix):
        swap = self.get_canvas(matrix)
        text_color = graphics.Color(150, 80, 0)

        graphics.DrawText(swap, self.font, 10, self.font.baseline - 2, text_color, "Goodbye")
        graphics.DrawText(swap, self.font, 18, self.font.baseline + 10, text_color, "See U")
        graphics.DrawText(swap, self.font, 15, self.font.baseline + 21, text_color, "Later!")

        self.swap_canvas(matrix, swap)
        time.sleep(5)
