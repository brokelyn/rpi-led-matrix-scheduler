import time
from rgbmatrix import graphics
import ping3
import settings


class StandbyService:

    def __init__(self):
        self.add_fnc = None
        self.rmv_fnc = None
        self.fnc_id = None
        self.online = True

    def ping(self, ip, n):
        counter = 0
        for i in range(n):
            try:
                result = ping3.ping(ip, unit="ms", timeout=5, size=2)
            except:
                counter += 1
            if not result:  # inactive
                counter += 1
        return counter

    def init(self, add_loop, rmv_loop):
        self.add_fnc = add_loop
        self.rmv_fnc = rmv_loop

    def service(self, add_event):
        while True:
            if self.online:
                if self.fnc_id:
                    self.rmv_fnc(self.fnc_id)
                    add_event(1, self.welcome)
                while True:
                    if self.ping("192.168.0.241", 5) == 5:
                        self.online = False
                        break
                    time.sleep(30)
            else:
                add_event(1, self.goodbye)
                self.fnc_id = self.add_fnc(1, self.standby)
                while True:
                    if self.ping("192.168.0.241", 5) == 0:
                        self.online = True
                        break
                    time.sleep(30)

    def standby(self, matrix):
        swap = matrix.CreateFrameCanvas()
        swap.Clear()
        matrix.SwapOnVSync(swap)
        time.sleep(5)

    def welcome(self, matrix):
        swap = matrix.CreateFrameCanvas()

        font = graphics.Font()
        font.LoadFont(settings.FONT_PATH + "6x13B.bdf")
        text_color = graphics.Color(170, 0, 170)

        swap.Clear()

        graphics.DrawText(swap, font, 10, font.baseline - 2, text_color, "Welcome")
        graphics.DrawText(swap, font, 20, font.baseline + 8, text_color, "back")
        graphics.DrawText(swap, font, 2, font.baseline + 19, text_color, "Was gehtn?")

        matrix.SwapOnVSync(swap)
        time.sleep(5)

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
        time.sleep(4)