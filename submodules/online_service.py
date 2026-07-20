import time
from rgbmatrix import graphics
from submodule import Submodule, load_font
import ping3


class OnlineService(Submodule):

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)
        self.fontBold = load_font("6x13B.bdf")
        self.font = load_font("5x8.bdf")
        add_loop(8, self.display_ping_test)

    @staticmethod
    def draw_cross(canvas, x, y):
        red = graphics.Color(200, 0, 0)

        graphics.DrawLine(canvas, x, y, x + 5, y + 5, red)
        graphics.DrawLine(canvas, x + 5, y, x, y + 5, red)

    @staticmethod
    def draw_check(canvas, x, y):
        green = graphics.Color(0, 200, 0)

        graphics.DrawLine(canvas, x, y + 5, x - 2, y + 3, green)
        graphics.DrawLine(canvas, x + 5, y, x, y + 5, green)

    def display_ping_test(self, matrix):
        header_color = graphics.Color(100, 100, 100)
        text_color = graphics.Color(100, 0, 190)
        red = graphics.Color(200, 0, 0)
        green = graphics.Color(0, 200, 0)
        yellow = graphics.Color(200, 140, 0)

        router_result = None
        google_result = None
        google_done = False

        # double buffering hands back a stale canvas after every swap, so each
        # frame redraws the full screen with the results gathered so far
        def draw(canvas):
            canvas.Clear()

            graphics.DrawText(canvas, self.fontBold, 7, self.fontBold.baseline - 2, header_color, "Services")
            graphics.DrawText(canvas, self.font, 0, self.font.baseline + 9, text_color, "Router:")
            graphics.DrawText(canvas, self.font, 0, self.font.baseline + 17, text_color, "google:")
            graphics.DrawText(canvas, self.font, 0, self.font.baseline + 24, text_color, "ping ms:")

            if router_result is not None:
                if router_result:
                    OnlineService.draw_check(canvas, 55, 10)
                else:
                    OnlineService.draw_cross(canvas, 55, 10)

            if google_done:
                if not google_result:
                    OnlineService.draw_cross(canvas, 55, 18)
                    graphics.DrawText(canvas, self.font, 52, self.font.baseline + 25, red, "to")
                else:
                    OnlineService.draw_check(canvas, 55, 18)
                    if google_result < 25:
                        graphics.DrawText(canvas, self.font, 52, self.font.baseline + 25, green, str(round(google_result)))
                    elif google_result < 75:
                        graphics.DrawText(canvas, self.font, 52, self.font.baseline + 25, yellow, str(round(google_result)))
                    elif google_result < 100:
                        graphics.DrawText(canvas, self.font, 52, self.font.baseline + 25, red, str(round(google_result)))
                    else:
                        graphics.DrawText(canvas, self.font, 49, self.font.baseline + 25, red, str(round(google_result)))

        swap = self.get_canvas(matrix)
        draw(swap)
        swap = self.swap_canvas(matrix, swap)
        time.sleep(1)

        router_result = ping3.ping("192.168.0.1", unit="ms", timeout=1, size=3) or False
        draw(swap)
        swap = self.swap_canvas(matrix, swap)
        time.sleep(1)

        google_result = ping3.ping("8.8.8.8", unit="ms", timeout=3, size=3)
        google_done = True
        draw(swap)
        swap = self.swap_canvas(matrix, swap)
        time.sleep(4)
