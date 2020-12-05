import time
from rgbmatrix import graphics
from submodule import Submodule
import settings
import ping3


class OnlineService(Submodule):

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)
        add_loop(8, self.display_ping_test)

    @staticmethod
    def draw_cross(matrix, x, y):
        red = graphics.Color(200, 0, 0)

        graphics.DrawLine(matrix, x, y, x + 5, y + 5, red)
        graphics.DrawLine(matrix, x + 5, y, x, y + 5, red)

    @staticmethod
    def draw_check(matrix, x, y):
        green = graphics.Color(0, 200, 0)

        graphics.DrawLine(matrix, x, y + 5, x - 2, y + 3, green)
        graphics.DrawLine(matrix, x + 5, y, x, y + 5, green)

    def display_ping_test(self, matrix):
        swap = matrix.CreateFrameCanvas()

        fontBold = graphics.Font()
        fontBold.LoadFont(settings.FONT_PATH + "6x13B.bdf")
        font = graphics.Font()
        font.LoadFont(settings.FONT_PATH + "5x8.bdf")
        header_color = graphics.Color(100, 100, 100)
        text_color = graphics.Color(100, 0, 190)
        red = graphics.Color(200, 0, 0)
        green = graphics.Color(0, 200, )
        yellow = graphics.Color(200, 140, 0)

        graphics.DrawText(swap, fontBold, 7, fontBold.baseline - 2, header_color, "Services")
        graphics.DrawText(swap, font, 0, font.baseline + 9, text_color, "Router:")
        graphics.DrawText(swap, font, 0, font.baseline + 17, text_color, "google:")
        graphics.DrawText(swap, font, 0, font.baseline + 24, text_color, "ping ms:")

        matrix.SwapOnVSync(swap)

        time.sleep(1)

        result = ping3.ping("192.168.0.1", unit="ms", timeout=1, size=3)
        if not result or result is None:
            OnlineService.draw_cross(swap, 55, 10)
        else:
            OnlineService.draw_check(swap, 55, 10)

        matrix.SwapOnVSync(swap)
        time.sleep(1)

        result = ping3.ping("8.8.8.8", unit="ms", timeout=3, size=3)
        if not result or result is None:
            OnlineService.draw_cross(swap, 55, 18)
        else:
            OnlineService.draw_check(swap, 55, 18)

        if not result or result is None:
            graphics.DrawText(swap, font, 52, font.baseline + 25, red, "to")
        else:
            if result < 25:
                graphics.DrawText(swap, font, 52, font.baseline + 25, green, str(round(result)))
            elif result < 75:
                graphics.DrawText(swap, font, 52, font.baseline + 25, yellow, str(round(result)))
            elif result < 100:
                graphics.DrawText(swap, font, 52, font.baseline + 25, red, str(round(result)))
            else:
                graphics.DrawText(swap, font, 49, font.baseline + 25, red, str(round(result)))

        matrix.SwapOnVSync(swap)
        time.sleep(4)
