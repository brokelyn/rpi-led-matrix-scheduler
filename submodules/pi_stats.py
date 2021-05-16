import time
from submodule import Submodule
from rgbmatrix import graphics
from PIL import Image, ImageSequence
import settings
import psutil


class PiStats(Submodule):

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)

        try:
            image = Image.open(settings.IMAGES_PATH + 'rpi.png')
            image = image.resize((9, 10))
            self.rgb_image = image.convert('RGB')
        except FileNotFoundError:
            print('Raspberry Pi image not found')

        add_loop(5.0, self.display_stats)

    def display_stats(self, matrix):
        for i in range(10):
            cpu_perc = int(psutil.cpu_percent())
            cpu_temp = int(psutil.sensors_temperatures()['cpu_thermal'][0].current)
            mem_perc = int(psutil.virtual_memory().percent)

            swap = matrix.CreateFrameCanvas()

            font = graphics.Font()
            font.LoadFont(settings.FONT_PATH + "6x13B.bdf")
            font2 = graphics.Font()
            font2.LoadFont(settings.FONT_PATH + "6x13.bdf")

            graphics.DrawText(swap, font, 5, font.baseline - 2, graphics.Color(100, 100, 100), " Pi Stat")

            graphics.DrawText(swap, font, 0, font.baseline * 2, graphics.Color(0, 180, 120), "CPU")
            graphics.DrawText(swap, font2, 0, font.baseline * 3 - 1, graphics.Color(0, 150, 40), str(cpu_perc) + '%')

            graphics.DrawText(swap, font, 24, font.baseline * 2, graphics.Color(130, 100, 10), "MEM")
            graphics.DrawText(swap, font2, 24, font.baseline * 3 - 1, graphics.Color(100, 50, 0), str(mem_perc) + '%')

            graphics.DrawText(swap, font, 46, font.baseline * 2, graphics.Color(140, 10, 10), "TMP")
            graphics.DrawText(swap, font2, 46, font.baseline * 3 - 1, graphics.Color(100, 0, 0), str(cpu_temp) + '°')

            matrix.SwapOnVSync(swap)
            matrix.SetImage(self.rgb_image, -1, -1, unsafe=False)
            matrix.SetImage(self.rgb_image, 55, -1, unsafe=False)
            time.sleep(0.7)
