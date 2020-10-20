import time
from rgbmatrix import graphics
from subtask import Subtask
import queue
import collections
import settings
import subprocess


class NetworkTracker(Subtask):

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)
        add_loop(4.5, self.display_connected)

        self.new_devices = queue.Queue()
        self.old_devices = queue.Queue()
        self.active_devices = {}

    @staticmethod
    def discover_network():
        cmd = ['sudo', 'nmap', '-sP', '--system-dns', '192.168.0.1/24']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = proc.communicate()

        if error.decode('utf-8') != '':
            print("ERROR: " + error.decode('utf-8'))
            return

        str_output = output.decode("utf-8")
        lines = str_output.splitlines()
        discovery = lines[1:]
        devices = {}

        for i in range(0, len(discovery), 3):
            hostname = discovery[i].split(' ')[4]

            if '192.168.0.' not in hostname:
                ip = discovery[i].split('(')[1]
                ip = ip.split(')')[0]
            else:
                ip = hostname
                hostname = 'Unknown'

            manufacturer = discovery[i + 2].split('(')[1]
            manufacturer = manufacturer.split(')')[0]

            if hostname == 'Unknown':
                devices[ip] = manufacturer
            else:
                devices[ip] = hostname.replace('.pihole', '')

        return devices

    def service(self):
        while True:
            average_devices = {}
            for r in range(2):
                devices = NetworkTracker.discover_network()
                average_devices = {**average_devices, **devices}

                time.sleep(3)

            for key in self.active_devices.keys():  # offline since last check
                if key not in average_devices.keys():
                    self.old_devices.put([key, self.active_devices[key]])
                    self.active_devices.pop(key)
                    self.add_event_fnc(2, self.display_old)

            for key in average_devices.keys():  # online since last check
                if key not in self.active_devices.keys():
                    self.active_devices[key] = [average_devices[key], time.perf_counter()]
                    self.new_devices.put([key, average_devices[key]])
                    self.add_event_fnc(2, self.display_new)

            time.sleep(120)

    def display_connected(self, matrix):
        swap = matrix.CreateFrameCanvas()

        font1 = graphics.Font()
        font1.LoadFont(settings.FONT_PATH + "5x8.bdf")
        font2 = graphics.Font()
        font2.LoadFont(settings.FONT_PATH + "4x6.bdf")

        device_color = graphics.Color(0, 150, 0)
        up_color = graphics.Color(125, 0, 125)
        text_color = graphics.Color(0, 150, 120)

        def draw_devices(offset):
            swap.Clear()
            line = 0

            graphics.DrawText(swap, font1, 13, font1.baseline - offset, text_color, "Network")

            for ip in collections.OrderedDict(sorted(self.active_devices.items())):
                device = self.active_devices[ip]
                online_min = int((time.perf_counter() - device[1]) / 60)
                y_position = font2.baseline + ((line + 1) * 7) - offset + 2

                graphics.DrawText(swap, font2, 0, y_position, device_color, device[0][:11])

                if online_min > 59:
                    online_hours = int(online_min / 60)
                    online_min = int(((online_min % 60) / 60) * 10)
                    up_text = str(online_hours) + "." + str(online_min) + "h"
                else:
                    up_text = str(online_min) + "m"

                graphics.DrawText(swap, font2, 52, y_position, up_color, up_text)
                line += 1

        draw_devices(0)
        matrix.SwapOnVSync(swap)
        time.sleep(3)

        if len(self.active_devices) > 4:
            for r in range((len(self.active_devices) - 4) * 9 + 1):
                draw_devices(r)

                matrix.SwapOnVSync(swap)
                time.sleep(0.15)

        time.sleep(3)

    def display_new(self, matrix):
        swap = matrix.CreateFrameCanvas()

        font1 = graphics.Font()
        font1.LoadFont(settings.FONT_PATH + "5x8.bdf")

        text_color = graphics.Color(0, 150, 0)
        ip_color = graphics.Color(125, 0, 200)

        swap.Clear()

        device = self.new_devices.get()

        graphics.DrawText(swap, font1, 0, font1.baseline + 0, ip_color, device[1])
        graphics.DrawText(swap, font1, 0, font1.baseline + 10, text_color, "Connected")
        graphics.DrawText(swap, font1, 0, font1.baseline + 21, ip_color, device[0])

        matrix.SwapOnVSync(swap)

        time.sleep(3)

    def display_old(self, matrix):
        swap = matrix.CreateFrameCanvas()

        font1 = graphics.Font()
        font1.LoadFont(settings.FONT_PATH + "5x8.bdf")

        text_color = graphics.Color(150, 0, 0)
        ip_color = graphics.Color(0, 200, 0)

        swap.Clear()

        device = self.old_devices.get()

        graphics.DrawText(swap, font1, 0, font1.baseline + 1, ip_color, device[1])
        graphics.DrawText(swap, font1, 0, font1.baseline + 10, text_color, "Disconnected")
        graphics.DrawText(swap, font1, 0, font1.baseline + 21, ip_color, device[0])

        matrix.SwapOnVSync(swap)

        time.sleep(3)
