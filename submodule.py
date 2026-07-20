import settings


class Submodule:

    # Web-editable settings: subclasses declare
    #   OPTIONS = {'key': {'label': ..., 'default': ..., 'min': ..., 'max': ..., 'step': ...}}
    # and read the current values from self.options['key']. The scheduler
    # updates that dict in place when modules.conf changes, so values read
    # inside a display loop apply live.
    OPTIONS = {}

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
        # the scheduler pre-sets self.options before __init__ runs; this
        # fallback keeps modules working when constructed directly
        if not hasattr(self, 'options'):
            self.options = {key: meta['default'] for key, meta in self.OPTIONS.items()}

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
