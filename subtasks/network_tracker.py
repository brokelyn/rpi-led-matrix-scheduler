import time
from rgbmatrix import graphics
import queue
import ping3
import collections
import settings


class NetworkTracker:

    def __init__(self):
        self.new_devices = queue.Queue()
        self.old_devices = queue.Queue()
        self.active_devices = {}

    def ping(self, ip, n):
        counter = 0
        for i in range(n):
            try:
                result = ping3.ping(ip, unit="ms", timeout=1, size=2)
            except:
                counter += 1
            if not result:  # inactive
                counter += 1
        return counter

    def init(self, add_loop, rmv_loop):
        add_loop(4, self.display_connected)

    def service(self, add_event):
        while True:
            for n in range(1, 255):
                ip = "192.168.0.{0}".format(n)
                result = self.ping(ip, 1)
                if result == 1:  # inactive
                    if ip in self.active_devices:
                        if self.ping(ip, 3) == 3:
                            self.active_devices.pop(n)
                            self.old_devices.put(ip)
                            add_event(2, self.display_old)
                else:  # active
                    if ip not in self.active_devices:
                        if self.ping(ip, 3) == 0:
                            self.active_devices[n] = time.perf_counter()
                            self.new_devices.put(ip)
                            add_event(2, self.display_new)

            time.sleep(120)

    def display_connected(self, matrix):
        swap = matrix.CreateFrameCanvas()

        font = graphics.Font()
        font.LoadFont(settings.FONT_PATH + "5x8.bdf")
        ip_color = graphics.Color(0, 150, 0)
        text_color = graphics.Color(0, 150, 120)

        swap.Clear()
        line = 0

        graphics.DrawText(swap, font, 0, font.baseline, text_color, "Network:")

        for ip in collections.OrderedDict(sorted(self.active_devices.items())):
            online_duration = int((time.perf_counter() - self.active_devices[ip]) / 60)
            text = str(ip) + " " * (3 - len(str(ip))) + " up " + str(online_duration) + "min"
            graphics.DrawText(swap, font, 0, font.baseline + ((line + 1) * 8), ip_color, text)
            line += 1

        matrix.SwapOnVSync(swap)
        time.sleep(3)

        if len(self.active_devices) > 3:
            for r in range((len(self.active_devices) - 3) * 8 + 1):
                matrix.Clear()
                graphics.DrawText(swap, font, 0, font.baseline - r, text_color, "Network:")
                line = 0

                for ip in collections.OrderedDict(sorted(self.active_devices.items())):
                    online_duration = int((time.perf_counter() - self.active_devices[ip]) / 60)
                    text = str(ip) + " " * (3 - len(str(ip))) + " up " + str(online_duration) + "min"
                    graphics.DrawText(swap, font, 0, font.baseline + ((line + 1) * 8) - r, ip_color, text)
                    line += 1

                matrix.SwapOnVSync(swap)
                time.sleep(0.2)

        time.sleep(3)

    def display_new(self, matrix):
        swap = matrix.CreateFrameCanvas()

        font = graphics.Font()
        font.LoadFont(settings.FONT_PATH + "5x8.bdf")
        text_color = graphics.Color(0, 150, 75)
        ip_color = graphics.Color(0, 250, 0)

        swap.Clear()

        graphics.DrawText(swap, font, 0, font.baseline, text_color, "New Device")
        graphics.DrawText(swap, font, 0, font.baseline + 9, text_color, "Connected")
        graphics.DrawText(swap, font, 0, font.baseline + 21, ip_color, self.new_devices.get())

        matrix.SwapOnVSync(swap)

        time.sleep(3)

    def display_old(self, matrix):
        swap = matrix.CreateFrameCanvas()

        font = graphics.Font()
        font.LoadFont(settings.FONT_PATH + "5x8.bdf")
        text_color = graphics.Color(0, 150, 75)
        ip_color = graphics.Color(0, 250, 0)

        swap.Clear()

        graphics.DrawText(swap, font, 0, font.baseline, text_color, "Device")
        graphics.DrawText(swap, font, 0, font.baseline + 9, text_color, "Disconnected")
        graphics.DrawText(swap, font, 0, font.baseline + 21, ip_color, self.old_devices.get())

        matrix.SwapOnVSync(swap)

        time.sleep(3)
