import time
from rgbmatrix import graphics
from submodule import Submodule, load_font
from datetime import datetime


class Clock(Submodule):

    OPTIONS = {
        'priority': {'label': 'Priority', 'default': 2, 'min': 1.5, 'max': 10, 'step': 0.5},
        'duration': {'label': 'Duration s', 'default': 8, 'min': 2, 'max': 120, 'step': 1},
    }

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)
        self.font = load_font("6x13B.bdf")
        add_loop(self.options['priority'], self.display_clock)

    def display_clock(self, matrix):
        swap = self.get_canvas(matrix)

        date_color = graphics.Color(120, 0, 190)
        day_color = graphics.Color(100, 130, 130)

        for i in range(int(self.options['duration'])):
            now = datetime.now()

            swap.Clear()

            graphics.DrawText(swap, self.font, 2, self.font.baseline - 2, date_color, now.strftime("%a %d %b"))
            graphics.DrawText(swap, self.font, 4, self.font.baseline + 9, day_color, now.strftime(" Day %j"))
            graphics.DrawText(swap, self.font, 2, self.font.baseline + 21, date_color, now.strftime(" %H %M %S"))

            swap = self.swap_canvas(matrix, swap)
            time.sleep(1)
