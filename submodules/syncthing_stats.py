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

        self.base_url = 'https://' + settings.SYNCTHING_IP # always refer to local syncthing
        self.headers = {'X-API-Key': settings.SYNCTHING_API_KEY}

        self.is_active = False
        self.devices = {}
        self.my_device_id = None

        add_loop(5, self.sync_status)

        try:
            self.image = Image.open(settings.IMAGES_PATH + 'syncthing.jpg')
            self.image = self.image.resize((8, 9))
            self.image = self.image.convert('RGB')
        except FileNotFoundError:
            print('Pi-Hole image not found')

        requests.packages.urllib3.disable_warnings()

        response = requests.get(self.base_url + '/rest/system/status', headers=self.headers, verify=False)
        json_data = response.json()
        self.my_device_id = json_data['myID']

        response = requests.get(self.base_url + '/rest/system/config', headers=self.headers, verify=False)
        json_data = response.json()

        for device in json_data['devices']:
            if device['deviceID'] != self.my_device_id:
                self.devices[device['deviceID']] = {'name': device['name']}

        self.request_connections()

    def request_full_completion(self):
        for device_id in self.devices.keys():
            self.request_completion(device_id)

    def request_completion(self, device_id):
        def request(context, device_id):
            url = context.base_url + '/rest/db/completion'
            parameters = {'device': device_id}

            response = requests.get(url, headers=context.headers, params=parameters, verify=False)
            json_data = response.json()
            with lock:
                context.devices[device_id]['completion'] = json_data['completion']
                context.devices[device_id]['needItems'] = json_data['needItems']
                context.devices[device_id]['needDeletes'] = json_data['needDeletes']

        thread = threading.Thread(target=request, args=(self, device_id, ))
        thread.start()

    def request_connections(self):
        url = self.base_url + '/rest/system/connections'

        response = requests.get(url, headers=self.headers, verify=False)
        connection_data = response.json()
        with lock:
            for device_id in connection_data['connections']:
                if device_id != self.my_device_id:
                    self.devices[device_id]['connected'] = connection_data['connections'][device_id]['connected']
                    self.devices[device_id]['paused'] = connection_data['connections'][device_id]['paused']

    def service(self):
        last_id = 0

        while True:
            self.request_connections()
            self.request_full_completion()

            url = self.base_url + '/rest/events'
            parameters = {'events': 'ItemStarted', 'since': last_id, 'limit': 1, 'timeout': 10}

            response = requests.get(url , headers=self.headers, params=parameters, verify=False)

            json = response.json()
            if len(json) > 0:
                last_id = json[len(json) - 1]['id']
                if not self.is_active:
                    self.is_active = True
                    self.add_event(2, self.sync_action)

                    self.request_full_completion()

                    while self.is_active:
                        time.sleep(1)

    def sync_action(self, matrix):
        self.request_full_completion()
        time.sleep(0.1) # wait for result of api request

        for device_id in self.devices:
            for i in range(6):
                try:
                    completion = int(self.devices[device_id]['completion'])
                except KeyError:
                    completion = 0

                if completion == 100:
                    break

                self.display_status(matrix, device_id)
                time.sleep(1)

                self.request_completion(device_id)


        self.is_active = False

    def sync_status(self, matrix):
        self.request_full_completion()

        for device_id in self.devices:
            for i in range(4):
                self.display_status(matrix, device_id)
                time.sleep(1)
                self.request_completion(device_id)

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

        device_name = self.devices[device_id]['name'][:5]

        graphics.DrawText(swap, font, 3, font.baseline - 2, graphics.Color(50, 50, 180), " Syncthing")
        graphics.DrawText(swap, font, 0, font.baseline * 2, graphics.Color(120, 120, 120), device_name)
        graphics.DrawText(swap, font2, 41, font.baseline * 2, graphics.Color(80, 120, 80), completion)

        if self.devices[device_id]['connected'] and not self.devices[device_id]['paused'] and completion != '100%':
            graphics.DrawText(swap, font, 0, font.baseline * 3 - 1, graphics.Color(20, 20, 120), "I")
            graphics.DrawText(swap, font2, 8, font.baseline * 3 - 1, graphics.Color(50, 50, 170), need_items)
            graphics.DrawText(swap, font, 38, font.baseline * 3 - 1, graphics.Color(100, 20, 20), "D")
            graphics.DrawText(swap, font2, 47, font.baseline * 3 - 1, graphics.Color(170, 60, 60), need_delete)
        elif self.devices[device_id]['paused']:
            graphics.DrawText(swap, font, 0, font.baseline * 3 - 1, graphics.Color(150, 85, 0), "Paused")
        elif not self.devices[device_id]['connected']:
            graphics.DrawText(swap, font, 0, font.baseline * 3 - 1, graphics.Color(150, 10, 0), "Offline")
        elif completion == '100%':
            graphics.DrawText(swap, font, 0, font.baseline * 3 - 1, graphics.Color(10, 120, 10), "Up to Date")

        matrix.SwapOnVSync(swap)
        matrix.SetImage(self.image, unsafe=False)
