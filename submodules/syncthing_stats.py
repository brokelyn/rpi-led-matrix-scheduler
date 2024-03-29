import time
from submodule import Submodule
from rgbmatrix import graphics
from PIL import Image
import settings
import requests
import threading

lock = threading.Lock()


class StatsSyncthing(Submodule):

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)

        # always refer to local syncthing
        self.base_url = 'https://' + settings.SYNCTHING_IP
        self.headers = {'X-API-Key': settings.SYNCTHING_API_KEY}

        self.is_active = False
        self.devices = {}
        self.my_device_id = None
        self.syncthing_online = False

        self.is_init_done = False

        add_loop(5, self.sync_status)

        try:
            self.image = Image.open(settings.IMAGES_PATH + 'syncthing.jpg')
            self.image = self.image.resize((8, 9))
            self.image = self.image.convert('RGB')
        except FileNotFoundError:
            print('Pi-Hole image not found')

        requests.packages.urllib3.disable_warnings()

    def request_full_completion(self, lazy=False):
        for device_id in self.devices.keys():
            if lazy:
                thread = self.request_completion(device_id)
                thread.join()
            else:
                self.request_completion(device_id)

    def request_completion(self, device_id):
        def request(context, device_id):
            url = context.base_url + '/rest/db/completion'
            parameters = {'device': device_id}

            try:
                response = requests.get(
                    url, headers=context.headers, params=parameters, verify=False)
                json_data = response.json()

                with lock:
                    context.devices[device_id]['completion'] = json_data['completion']
                    context.devices[device_id]['needItems'] = json_data['needItems']
                    context.devices[device_id]['needDeletes'] = json_data['needDeletes']
                self.syncthing_online = True
            except requests.exceptions.ConnectionError:
                self.syncthing_online = False

        thread = threading.Thread(target=request, args=(self, device_id, ))
        thread.start()
        return thread

    def request_connections(self):
        url = self.base_url + '/rest/system/connections'

        try:
            response = requests.get(url, headers=self.headers, verify=False)
            connection_data = response.json()
            with lock:
                for device_id in connection_data['connections']:
                    if device_id != self.my_device_id:
                        self.devices[device_id]['connected'] = connection_data['connections'][device_id]['connected']
                    else:
                        self.devices[device_id]['connected'] = True

                    self.devices[device_id]['paused'] = connection_data['connections'][device_id]['paused']
            self.syncthing_online = True
        except requests.exceptions.ConnectionError:
            self.syncthing_online = False

    def lazy_init(self):
        while True:
            try:
                response = requests.get(
                    self.base_url + '/rest/system/status', headers=self.headers, verify=False)
                json_data = response.json()
                self.my_device_id = json_data['myID']

                response = requests.get(
                    self.base_url + '/rest/system/config', headers=self.headers, verify=False)
                json_data = response.json()

                for device in json_data['devices']:
                    self.devices[device['deviceID']] = {'name': device['name']}

                self.request_connections()
                self.syncthing_online = True
                return
            except requests.exceptions.ConnectionError:
                time.sleep(15)

    def service(self):
        self.lazy_init()

        last_id = 0
        url = self.base_url + '/rest/events'
        while True:
            self.request_connections()
            self.request_full_completion(lazy=True)

            parameters = {'events': 'ItemStarted',
                          'since': last_id, 'limit': 1, 'timeout': 15}

            try:
                response = requests.get(
                    url, headers=self.headers, params=parameters, verify=False)

                self.syncthing_online = True

                json = response.json()
                if len(json) > 0:
                    last_id = json[len(json) - 1]['id']
                    if not self.is_active:
                        self.is_active = True
                        self.add_event(2, self.sync_action)

                        self.request_full_completion(lazy=True)

                        while self.is_active:
                            time.sleep(1)
            except requests.exceptions.ConnectionError:
                self.syncthing_online = False
                time.sleep(15)

    def sync_action(self, matrix):
        self.request_full_completion()
        time.sleep(0.25)  # wait for result of api request

        for device_id in self.devices:
            for i in range(6):
                try:
                    completion = int(self.devices[device_id]['completion'])
                except KeyError:
                    completion = 0

                if completion == 100 or not self.devices[device_id]['connected']:
                    break

                self.display_status(matrix, device_id)
                time.sleep(1)

                self.request_completion(device_id)

        self.is_active = False

    def sync_status(self, matrix):
        self.request_full_completion()

        if self.syncthing_online:
            for device_id in self.devices:
                for i in range(3):
                    self.display_status(matrix, device_id)
                    time.sleep(1)
                    self.request_completion(device_id)
        else:
            self.display_offline(matrix)
            time.sleep(7)

    def display_offline(self, matrix):
        swap = matrix.CreateFrameCanvas()

        font = graphics.Font()
        font.LoadFont(settings.FONT_PATH + "6x13B.bdf")

        font2 = graphics.Font()
        font2.LoadFont(settings.FONT_PATH + "4x6.bdf")

        graphics.DrawText(swap, font, 3, font.baseline - 2,
                          graphics.Color(50, 50, 180), " Syncthing")
        graphics.DrawText(swap, font2, 0, font.baseline * 2,
                          graphics.Color(120, 120, 120), settings.SYNCTHING_IP)
        graphics.DrawText(swap, font, 11, font.baseline * 3 - 1,
                          graphics.Color(200, 25, 25), "Offline")

        matrix.SwapOnVSync(swap)
        matrix.SetImage(self.image, unsafe=False)

    def display_status(self, matrix, device_id):
        try:
            completion = str(int(self.devices[device_id]['completion'])) + '%'
            need_items = str(self.devices[device_id]['needItems'])
            need_delete = str(self.devices[device_id]['needDeletes'])
        except KeyError:
            completion = 'Err'
            need_items = 'Err'
            need_delete = 'Err'

        swap = matrix.CreateFrameCanvas()

        font = graphics.Font()
        font.LoadFont(settings.FONT_PATH + "6x13B.bdf")
        font2 = graphics.Font()
        font2.LoadFont(settings.FONT_PATH + "6x13.bdf")

        device_name = self.devices[device_id]['name'][:6]

        graphics.DrawText(swap, font, 3, font.baseline - 2,
                          graphics.Color(50, 50, 180), " Syncthing")
        graphics.DrawText(swap, font, 0, font.baseline * 2,
                          graphics.Color(120, 120, 120), device_name)
        graphics.DrawText(swap, font2, 41, font.baseline * 2,
                          graphics.Color(80, 100, 80), completion)

        if self.devices[device_id]['connected'] and not self.devices[device_id]['paused'] and completion != '100%':
            graphics.DrawText(swap, font, 0, font.baseline *
                              3 - 1, graphics.Color(20, 20, 120), "I")
            graphics.DrawText(swap, font2, 8, font.baseline *
                              3 - 1, graphics.Color(50, 50, 170), need_items)
            graphics.DrawText(swap, font, 38, font.baseline *
                              3 - 1, graphics.Color(100, 20, 20), "D")
            graphics.DrawText(swap, font2, 47, font.baseline *
                              3 - 1, graphics.Color(170, 60, 60), need_delete)
        elif self.devices[device_id]['paused']:
            graphics.DrawText(swap, font, 0, font.baseline *
                              3 - 1, graphics.Color(150, 85, 0), "Paused")
        elif not self.devices[device_id]['connected']:
            graphics.DrawText(swap, font, 0, font.baseline *
                              3 - 1, graphics.Color(120, 10, 0), "Offline")
        elif completion == '100%':
            graphics.DrawText(swap, font, 0, font.baseline *
                              3 - 1, graphics.Color(10, 120, 10), "Up to Date")

        matrix.SwapOnVSync(swap)
        matrix.SetImage(self.image, unsafe=False)
