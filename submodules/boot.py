import time
from submodule import Submodule
import settings
from rgbmatrix import graphics
from PIL import Image, ImageSequence


class BootService(Submodule):

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)

        add_event(1, self.display_boot_animation)
        add_event(1, self.display_boot_info)

    def display_boot_animation(self, matrix):
        try:
            image = Image.open(settings.IMAGES_PATH + 'boot2.gif')
        except FileNotFoundError:
            print('Boot Animation not found')
            return

        for frame in range(0, image.n_frames):
            image.seek(frame)
            temp = image.copy()
            temp = temp.resize((64, 32))
            matrix.SetImage(temp.convert('RGB'), unsafe=False)

            time.sleep(0.025)

        matrix.Clear()

    def display_boot_info(self, matrix):
        swap = matrix.CreateFrameCanvas()

        fontBold = graphics.Font()
        fontBold.LoadFont(settings.FONT_PATH + "6x13B.bdf")
        font = graphics.Font()
        font.LoadFont(settings.FONT_PATH + "5x8.bdf")
        header_color = graphics.Color(0, 180, 20)
        text_color = graphics.Color(100, 0, 100)
        number_color = graphics.Color(100, 100, 100)

        graphics.DrawText(swap, fontBold, 5, fontBold.baseline - 2, header_color, "Boot Info")
        graphics.DrawText(swap, font, 1, font.baseline + 13, text_color, "Modules:")
        graphics.DrawText(swap, font, 54, font.baseline + 13, number_color, str(settings.LOADED_MODULES))
        graphics.DrawText(swap, font, 1, font.baseline + 22, text_color, "Services:")
        graphics.DrawText(swap, font, 54, font.baseline + 22, number_color, str(settings.RUNNING_SERVICES))

        matrix.SwapOnVSync(swap)

        time.sleep(5)

