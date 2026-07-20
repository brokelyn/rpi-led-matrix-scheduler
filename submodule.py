import settings


class Submodule:

    # The matrix never frees canvases returned by CreateFrameCanvas() until the
    # matrix itself is destroyed, so all modules share one off-screen canvas
    # instead of creating a new one on every display call. Display functions
    # only run on the scheduler thread, so no locking is needed.
    _canvas = None

    def __init__(self, add_loop, rmv_loop, add_event):
        self.add_loop = add_loop
        self.rmv_loop = rmv_loop
        self.add_event = add_event
        self.fnc_id = None

    def get_canvas(self, matrix):
        if Submodule._canvas is None:
            Submodule._canvas = matrix.CreateFrameCanvas()
        Submodule._canvas.Clear()
        return Submodule._canvas

    def swap_canvas(self, matrix, canvas):
        # the returned canvas is the one that just left the screen; its content
        # is one frame old, so redraw it completely before swapping again
        Submodule._canvas = matrix.SwapOnVSync(canvas)
        return Submodule._canvas


_fonts = {}


def load_font(name):
    # imported lazily so this module stays importable without the led binding
    from rgbmatrix import graphics

    if name not in _fonts:
        font = graphics.Font()
        font.LoadFont(settings.FONT_PATH + name)
        _fonts[name] = font
    return _fonts[name]
