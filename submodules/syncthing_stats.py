import time
from submodule import Submodule
from rgbmatrix import graphics
from PIL import Image
import settings
import requests
import threading


class StatsSyncthing(Submodule):

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)

        self.is_active = False
        self.response_code = None
        self.folder = [settings.SYNCTHING_FOLDER_ID1, settings.SYNCTHING_FOLDER_ID2]
        self.folder_names = [settings.SYNCTHING_FOLDER_NAME1, settings.SYNCTHING_FOLDER_NAME2]
        self.data = [{}, {}]

        add_loop(5.5, self.sync_status)

        try:
            self.image = Image.open(settings.IMAGES_PATH + 'syncthing.jpg')
            self.image = self.image.resize((8, 9))
            self.image = self.image.convert('RGB')
        except FileNotFoundError:
            print('Pi-Hole image not found')

        requests.packages.urllib3.disable_warnings()

    def request_completion(self, folder_id):
        def request(obj, folder_id):
            url = 'https://' + settings.SYNCTHING_IP + '/rest/db/completion'
            headers = {'X-API-Key': settings.SYNCTHING_API_KEY}
            parameters = {'folder': self.folder[folder_id]}

            response = requests.get(url, headers=headers, params=parameters, verify=False)
            obj.response_code = response.status_code
            obj.data[folder_id] = response.json()

        thread = threading.Thread(target=request, args=(self, folder_id, ))
        thread.start()

    def service(self):
        last_id = 0

        while True:
            url = 'https://' + settings.SYNCTHING_IP + '/rest/events'
            headers = {'X-API-Key': settings.SYNCTHING_API_KEY}
            parameters = {'events': 'ItemStarted', 'since': last_id, 'limit': 1}

            response = requests.get(url, headers=headers, params=parameters, verify=False)

            json = response.json()
            if len(json) > 0:
                last_id = json[len(json) - 1]['id']
                if not self.is_active:
                    self.is_active = True
                    self.add_event(2, self.sync_action)

                    for folder_id in range(len(self.folder)):
                        self.request_completion(folder_id)

                    while self.is_active:
                        time.sleep(1)

    def sync_action(self, matrix):
        for folder_id in range(len(self.folder)):
            for i in range(4):
                self.display_status(matrix, folder_id)
                self.request_completion(folder_id)
                time.sleep(2)

                try:
                    completion = int(self.data[folder_id]['completion'])
                except KeyError:
                    completion = 0

                if self.is_active and completion == 100:
                    break

        self.is_active = False

    def sync_status(self, matrix):
        for folder_id in range(len(self.folder)):
            for i in range(2):
                self.display_status(matrix, folder_id)
                self.request_completion(folder_id)
                time.sleep(2)

    def display_status(self, matrix, folder_id):
        try:
            completion = str(int(self.data[folder_id]['completion'])) + '%'
            need_items = str(self.data[folder_id]['needItems'])
            need_delete = str(self.data[folder_id]['needDeletes'])
        except KeyError:
            completion = 'Err'
            need_items = 'Err'
            need_delete = 'Err'

        swap = matrix.CreateFrameCanvas()

        font = graphics.Font()
        font.LoadFont(settings.FONT_PATH + "6x13B.bdf")
        font2 = graphics.Font()
        font2.LoadFont(settings.FONT_PATH + "6x13.bdf")

        folder_name = self.folder_names[folder_id][:5]

        graphics.DrawText(swap, font, 3, font.baseline - 2, graphics.Color(50, 50, 180), " Syncthing")
        graphics.DrawText(swap, font, 0, font.baseline * 2, graphics.Color(120, 120, 120), folder_name)
        graphics.DrawText(swap, font2, 41, font.baseline * 2, graphics.Color(80, 120, 80), completion)
        graphics.DrawText(swap, font, 0, font.baseline * 3 - 1, graphics.Color(20, 20, 120), "I")
        graphics.DrawText(swap, font2, 8, font.baseline * 3 - 1, graphics.Color(50, 50, 170), need_items)
        graphics.DrawText(swap, font, 38, font.baseline * 3 - 1, graphics.Color(100, 20, 20), "D")
        graphics.DrawText(swap, font2, 47, font.baseline * 3 - 1, graphics.Color(170, 60, 60), need_delete)

        matrix.SwapOnVSync(swap)
        matrix.SetImage(self.image, unsafe=False)
