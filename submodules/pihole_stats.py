import time
from submodule import Submodule, load_font
import settings
import requests
from rgbmatrix import graphics
from PIL import Image


class PiholeStats(Submodule):

    OPTIONS = {
        'priority': {'label': 'Priority', 'default': 4.5, 'min': 1.5, 'max': 10, 'step': 0.5},
        'duration': {'label': 'Duration s', 'default': 8, 'min': 2, 'max': 60, 'step': 2},
    }

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)

        self.font = load_font("6x13B.bdf")
        self.font2 = load_font("6x13.bdf")

        try:
            image = Image.open(settings.IMAGES_PATH + 'pi-hole.png')
            self.image = image.resize((8, 9)).convert('RGB')
        except FileNotFoundError:
            print('Pi-Hole image not found')
            self.image = None

        add_loop(self.options['priority'], self.display_stats)

    def display_stats(self, matrix):
        for i in range(max(1, int(self.options['duration'] / 2))):
            swap = self.get_canvas(matrix)

            graphics.DrawText(swap, self.font, 5, self.font.baseline - 2, graphics.Color(120, 120, 120), " Pi Hole")

            try:
                response = requests.get("http://" + settings.PI_HOLE_IP + "/admin/api.php?summaryRaw", timeout=3)
                json = response.json()
                queries_today = json['dns_queries_today']
                percentage_blocked = int(json['ads_percentage_today'])

                graphics.DrawText(swap, self.font, 0, self.font.baseline * 2 - 2, graphics.Color(0, 180, 120), "Query")
                graphics.DrawText(swap, self.font2, 35, self.font.baseline * 2 - 2, graphics.Color(0, 180, 20), str(queries_today))
                graphics.DrawText(swap, self.font, 0, self.font.baseline * 3 - 1, graphics.Color(140, 10, 10), "Blocked")
                graphics.DrawText(swap, self.font2, 47, self.font.baseline * 3 - 1, graphics.Color(120, 0, 0), str(percentage_blocked) + '%')

            except requests.exceptions.RequestException:
                graphics.DrawText(swap, self.font, 11, self.font.baseline * 3 - 1, graphics.Color(180, 10, 10), "Offline")

            if self.image is not None:
                swap.SetImage(self.image, unsafe=False)

            swap = self.swap_canvas(matrix, swap)
            time.sleep(2)
