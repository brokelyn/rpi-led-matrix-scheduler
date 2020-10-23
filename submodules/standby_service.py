import time
from rgbmatrix import graphics
from submodule import Submodule
import ping3
import settings


class StandbyService(Submodule):

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)
        self.online = True

    def ping(self, ip, n):
        counter = 0
        for i in range(n):
            try:
                result = ping3.ping(ip, unit="ms", timeout=5, size=2)
                if not result:  # inactive
                    counter += 1
            except:
                counter += 1
        return counter

    def service(self):
        while True:
            if self.online:
                if self.fnc_id:
                    self.rmv_loop(self.fnc_id)
                    self.add_event(1, self.welcome)
                while True:
                    if self.ping(settings.STANDBY_DEVICE_IP, 5) == 5:
                        self.online = False
                        break
                    time.sleep(40)
            else:
                self.add_event(1, self.goodbye)
                self.fnc_id = self.add_loop(1, self.standby)
                while True:
                    if self.ping(settings.STANDBY_DEVICE_IP, 1) == 0:
                        self.online = True
                        break
                    time.sleep(50)

    def standby(self, matrix):
        swap = matrix.CreateFrameCanvas()
        swap.Clear()
        matrix.SwapOnVSync(swap)
        time.sleep(15)

    def welcome(self, matrix):
        swap = matrix.CreateFrameCanvas()

        font = graphics.Font()
        font.LoadFont(settings.FONT_PATH + "6x13B.bdf")
        text_color = graphics.Color(170, 0, 170)

        swap.Clear()

        graphics.DrawText(swap, font, 10, font.baseline - 2, text_color, "Welcome")
        graphics.DrawText(swap, font, 20, font.baseline + 8, text_color, "back")
        graphics.DrawText(swap, font, 2, font.baseline + 19, text_color, "Was sgdn?")

        matrix.SwapOnVSync(swap)
        time.sleep(5.5)

    def goodbye(self, matrix):
        swap = matrix.CreateFrameCanvas()

        font = graphics.Font()
        font.LoadFont(settings.FONT_PATH + "6x13B.bdf")
        text_color = graphics.Color(150, 80, 0)

        swap.Clear()

        graphics.DrawText(swap, font, 10, font.baseline - 2, text_color, "Goodbye")
        graphics.DrawText(swap, font, 18, font.baseline + 10, text_color, "See U")
        graphics.DrawText(swap, font, 15, font.baseline + 21, text_color, "Later!")

        matrix.SwapOnVSync(swap)
        time.sleep(5)
