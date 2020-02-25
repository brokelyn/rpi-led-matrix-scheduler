import time
from rgbmatrix import graphics
from datetime import datetime
import settings


class Clock:

    def init(self, add_loop):
        add_loop(2, self.display_clock)

    def service(self, add_event):
        pass

    def display_clock(self, matrix):
        swap = matrix.CreateFrameCanvas()

        font = graphics.Font()
        font.LoadFont(settings.FONT_PATH + "6x13B.bdf")
        text_color = graphics.Color(130, 0, 190)

        for i in range(8):
            time_text1 = datetime.now().strftime("%j %b %y")
            time_text2 = datetime.now().strftime("%A")
            time_text3 = datetime.now().strftime("%H %M %S")

            swap.Clear()

            graphics.DrawText(swap, font, 0,  font.baseline - 2, text_color, time_text1)
            graphics.DrawText(swap, font, 0, font.baseline + 9, text_color, time_text2)
            graphics.DrawText(swap, font, 0, font.baseline + 21, text_color, time_text3)

            swap = matrix.SwapOnVSync(swap)
            time.sleep(1)
