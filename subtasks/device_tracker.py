import time
from rgbmatrix import graphics
import queue
import ping3
import threading
import settings


class DeviceTracker:

    def __init__(self):
        self.new_devices = queue.Queue()
        self.old_devices = queue.Queue()
        self.active_devices = list()

    def ping(self, ip, n):
        counter = 0
        for i in range(n):
            try:
                result = ping3.ping(ip, unit="ms", timeout=1, size=2)
            except:
                counter += 1
            if not result:  # inactive
                counter += 1
        if counter == 0:
            return True
        return False

    def init(self, add_loop):
        add_loop(4, self.display_connected)

    def service(self, add_event):
        while True:
            for n in range(1, 255):
                ip = "192.168.0.{0}".format(n)
                result = self.ping(ip, 1)
                if not result:  # inactive
                    if ip in self.active_devices:
                        if not self.ping(ip, 3):
                            self.active_devices.remove(ip)
                            self.old_devices.put(ip)
                            add_event(2, self.display_old)
                else:  # active
                    if ip not in self.active_devices:
                        if self.ping(ip, 3):
                            self.active_devices.append(ip)
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

        graphics.DrawText(swap, font, 0, font.baseline, text_color, "Network:")

        for i in range(len(self.active_devices)):
            graphics.DrawText(swap, font, 0, font.baseline + ((i + 1) * 8), ip_color, self.active_devices[i])

        matrix.SwapOnVSync(swap)
        time.sleep(3)

        if len(self.active_devices) > 3:
            for r in range((len(self.active_devices) - 3) * 8 + 1):
                matrix.Clear()
                graphics.DrawText(swap, font, 0, font.baseline - r, text_color, "Network:")

                for i in range(len(self.active_devices)):
                    graphics.DrawText(swap, font, 0, font.baseline + ((i + 1) * 8) - r, ip_color, self.active_devices[i])

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
