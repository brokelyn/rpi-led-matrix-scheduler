import time
from submodule import Submodule, load_font
from rgbmatrix import graphics
from PIL import Image
import settings
import psutil


class PiStats(Submodule):

    OPTIONS = {
        'priority': {'label': 'Priority', 'default': 5, 'min': 1.5, 'max': 10, 'step': 0.5},
        'duration': {'label': 'Duration s', 'default': 7, 'min': 3, 'max': 60, 'step': 1},
    }

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)

        self.font = load_font("6x13B.bdf")
        self.font2 = load_font("6x13.bdf")

        try:
            image = Image.open(settings.IMAGES_PATH + 'rpi.png')
            self.rgb_image = image.resize((9, 10)).convert('RGB')
        except FileNotFoundError:
            print('Raspberry Pi image not found')
            self.rgb_image = None

        add_loop(self.options['priority'], self.display_stats)

    def display_stats(self, matrix):
        for i in range(max(1, int(self.options['duration'] / 0.7))):
            cpu_perc = int(psutil.cpu_percent())
            cpu_temp = int(psutil.sensors_temperatures()['cpu_thermal'][0].current)
            mem_perc = int(psutil.virtual_memory().percent)

            swap = self.get_canvas(matrix)

            graphics.DrawText(swap, self.font, 5, self.font.baseline - 2, graphics.Color(100, 100, 100), " Pi Stat")

            graphics.DrawText(swap, self.font, 0, self.font.baseline * 2, graphics.Color(0, 180, 120), "CPU")
            graphics.DrawText(swap, self.font2, 0, self.font.baseline * 3 - 1, graphics.Color(0, 150, 40), str(cpu_perc) + '%')

            graphics.DrawText(swap, self.font, 24, self.font.baseline * 2, graphics.Color(130, 100, 10), "MEM")
            graphics.DrawText(swap, self.font2, 24, self.font.baseline * 3 - 1, graphics.Color(100, 50, 0), str(mem_perc) + '%')

            graphics.DrawText(swap, self.font, 46, self.font.baseline * 2, graphics.Color(140, 10, 10), "TMP")
            graphics.DrawText(swap, self.font2, 46, self.font.baseline * 3 - 1, graphics.Color(100, 0, 0), str(cpu_temp) + '°')

            if self.rgb_image is not None:
                swap.SetImage(self.rgb_image, -1, -1, unsafe=False)
                swap.SetImage(self.rgb_image, 55, -1, unsafe=False)

            swap = self.swap_canvas(matrix, swap)
            time.sleep(0.7)
