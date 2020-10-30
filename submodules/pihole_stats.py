import time
from submodule import Submodule
import settings
import requests
from rgbmatrix import graphics
from PIL import Image, ImageSequence


class PiholeStats(Submodule):

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)

        add_loop(4, self.display_stats)

    def display_stats(self, matrix):
        try:
            image = Image.open(settings.IMAGES_PATH + 'pi-hole.png')
            image = image.resize((8, 9))
        except FileNotFoundError:
            print('Pi-Hole image not found')
            return

        for i in range(4):
            response = requests.get("http://" + settings.PI_HOLE_IP + "/admin/api.php?summaryRaw")
            json = response.json()
            queries_today = json['dns_queries_today']
            percentage_blocked = json['ads_percentage_today']

            swap = matrix.CreateFrameCanvas()

            font = graphics.Font()
            font.LoadFont(settings.FONT_PATH + "6x13B.bdf")
            font2 = graphics.Font()
            font2.LoadFont(settings.FONT_PATH + "6x13.bdf")

            graphics.DrawText(swap, font, 5, font.baseline - 2, graphics.Color(120, 120, 120), " Pi Hole")
            graphics.DrawText(swap, font, 0, font.baseline * 2 - 2, graphics.Color(0, 180, 120), "Query")
            graphics.DrawText(swap, font2, 35, font.baseline * 2 - 2, graphics.Color(0, 180, 20), str(queries_today))
            graphics.DrawText(swap, font, 0, font.baseline * 3 - 1, graphics.Color(140, 10, 10), "Blocked")
            graphics.DrawText(swap, font2, 47, font.baseline * 3 - 1, graphics.Color(120, 0, 0), str(percentage_blocked)[:2] + '%')

            matrix.SwapOnVSync(swap)
            matrix.SetImage(image.convert('RGB'), unsafe=False)
            time.sleep(2)
