import time
from rgbmatrix import graphics
from datetime import datetime
import settings


class Clock:

    def init(self, add_loop, rmv_loop):
        add_loop(2, self.display_clock)

    def service(self, add_event):
        pass

    def display_clock(self, matrix):
        swap = matrix.CreateFrameCanvas()

        font = graphics.Font()
        font.LoadFont(settings.FONT_PATH + "6x13B.bdf")

        for i in range(8):
            time_text1 = datetime.now().strftime("%a %d %b")
            time_text2 = datetime.now().strftime(" Day %j")
            time_text3 = datetime.now().strftime(" %H %M %S")

            swap.Clear()

            graphics.DrawText(swap, font, 2,  font.baseline - 2, graphics.Color(120, 0, 190), time_text1)
            graphics.DrawText(swap, font, 4, font.baseline + 9, graphics.Color(80, 0, 130), time_text2)
            graphics.DrawText(swap, font, 2, font.baseline + 21, graphics.Color(120, 0, 190), time_text3)

            swap = matrix.SwapOnVSync(swap)
            time.sleep(1)
