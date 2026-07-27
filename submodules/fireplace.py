import time
import random
from submodule import Submodule

# heat 15..5 is fire, ramping white-hot -> yellow -> orange -> red -> a dim
# ember glow, heat 4..1 is what is left of it: the last levels desaturate from
# a warm ash tone into faint gray smoke. 0 is the black background.
PALETTE = [
    None,
    (11, 11, 12), (18, 17, 17), (28, 24, 22), (38, 27, 21),
    (70, 14, 4), (104, 22, 5), (142, 34, 6), (176, 56, 8),
    (204, 82, 10), (226, 108, 14), (242, 138, 24), (252, 168, 40),
    (255, 200, 80), (255, 230, 150), (255, 250, 220),
]
MAX_HEAT = len(PALETTE) - 1
SMOKE_MAX = 4

# a near-constant loss per row is what makes the color track the height: the
# flame runs through white, yellow, orange and red in the same order every time
# instead of scattering hot pixels all the way up to the tip
DECAY = (0, 1, 1, 1, 1, 1, 2, 2)          # avg 1.1 heat loss per row -> tall flames
SMOKE_DECAY = (0, 0, 1, 1, 1, 2)          # smoke cools slowly and lingers above
FLICKER = 3                               # how far the seed row dips below full heat

# each torch runs its own small fire grid, centered over the torch head. The
# grid is as wide as the fire size setting; everything derived from that width
# is built once per size and cached, since it only changes when the slider does.
BASE_W = 13     # the width the tables above are tuned for
_grids = {}


def stretch(decay, scale):
    """A decay table that spends the same total heat over `scale` times as many
    rows: idle rows appear for a bigger fire, steeper losses for a smaller one.
    Without this a wider fire would only get fatter, never taller.

    The remainder is carried between entries rather than rounded away, so the
    table keeps the ups and downs that make the tips flicker - and at scale 1
    it comes back out exactly as it went in."""
    table, carry = [], 0.0
    for value in decay:
        carry += value / scale
        step = int(carry)
        carry -= step
        table.append(step)
    return tuple(table)


def fire_grid(width):
    """-> (seed heat per column, edge cooling per column, decay, smoke decay)

    Bell seed: a flat-topped core of full heat over the torch head falling off
    to nothing at the grid edges, so the flame starts as a fat white-hot tongue
    and only widens further by drifting upwards."""
    if width not in _grids:
        center = (width - 1) / 2
        seed_max, edge_cooling = [], []
        for x in range(width):
            # the bell keeps the same share of the grid at every size
            d = abs(x - center) / (width / 3.25)
            seed_max.append(round(MAX_HEAT * max(0.0, 1 - d ** 3)))
            edge_cooling.append(1 if d > 1 else 0)
        scale = width / BASE_W
        _grids[width] = (seed_max, edge_cooling,
                         stretch(DECAY, scale), stretch(SMOKE_DECAY, scale))
    return _grids[width]


WOOD = (96, 56, 18)
WRAP = (156, 100, 36)   # the cloth-wrapped head the flame sits on


class _Torch:

    def __init__(self, base_x, tip_x, tip_y, fire_top, drift, width):
        self.tip_y = tip_y
        self.drift = drift
        self.height = tip_y - fire_top + 1
        self.width = width
        self.left = tip_x - width // 2
        (self.seed_max, self.edge_cooling,
         self.decay, self.smoke_decay) = fire_grid(width)

        # 2 px wide stick from the bottom edge up to the tip; the top two
        # rows are the brighter wrapped head
        self.stick = []
        for y in range(tip_y, 32):
            t = (31 - y) / (31 - tip_y)
            x = round(base_x + (tip_x - base_x) * t)
            color = WRAP if y <= tip_y + 1 else WOOD
            self.stick.append((x, y, color))
            self.stick.append((x + 1, y, color))


# drift picks the source cell below (x + drift), so extra +1 entries make the
# flame lean left and extra -1 entries make it lean right - matching the tilt
def build_torches(spacing, height, size):
    """spacing: outer tip distance from the center, height: how far the
    center tip sits above the bottom edge, size: fire grid width. The outer
    torches sit two rows lower and lean outwards by 3 px over their stick."""
    center_tip = 31 - height
    side_tip = min(29, center_tip + 2)
    rows = size / BASE_W    # a bigger fire needs a taller grid to rise in
    return [
        _Torch(34 - spacing, 31 - spacing, side_tip,          # left, leaning outwards
               max(1, side_tip - round(17 * rows)), (-1, 0, 0, 1, 1), size),
        _Torch(31, 31, center_tip,                            # center, upright and taller
               max(1, center_tip - round(19 * rows)), (-1, 0, 0, 0, 1), size),
        _Torch(28 + spacing, 31 + spacing, side_tip,          # right, leaning outwards
               max(1, side_tip - round(17 * rows)), (-1, -1, 0, 0, 1), size),
    ]


class Fireplace(Submodule):

    OPTIONS = {
        'priority': {'label': 'Priority', 'default': 4, 'min': 1.5, 'max': 10, 'step': 0.5},
        'embers':   {'label': 'Ember heat %', 'default': 100, 'min': 50, 'max': 100, 'step': 5},
        'flames':   {'label': 'Flame height', 'default': 3, 'min': 1, 'max': 4, 'step': 1},
        'size':     {'label': 'Fire size px', 'default': 13, 'min': 7, 'max': 21, 'step': 2},
        'spacing':  {'label': 'Spacing px', 'default': 10, 'min': 4, 'max': 22, 'step': 1},
        'height':   {'label': 'Height px', 'default': 8, 'min': 4, 'max': 14, 'step': 1},
        'duration': {'label': 'Duration s', 'default': 17, 'min': 5, 'max': 120, 'step': 1},
        'fps':      {'label': 'FPS', 'default': 15, 'min': 6, 'max': 30, 'step': 1},
    }

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)
        add_loop(self.options['priority'], self.display_fireplace)

    @staticmethod
    def step_fire(heat, torch, ember_scale, extra_cooling):
        # the tables are read once per cell, so keep them in locals
        width, drift = torch.width, torch.drift
        decay, smoke_decay = torch.decay, torch.smoke_decay
        seed_heat, edge_cooling = torch.seed_max, torch.edge_cooling
        last = width - 1

        # seed the bottom row (the torch head) with flickering heat
        height = len(heat)
        for x in range(width):
            seed_max = round(seed_heat[x] * ember_scale)
            heat[height - 1][x] = random.randint(max(0, seed_max - FLICKER), seed_max)

        # classic doom fire: heat rises, drifts sideways and cools down.
        # once a cell drops out of the fire range it lives on as smoke,
        # which cools much slower and so keeps drifting up a few rows
        # past the point where the flame has faded out
        for y in range(height - 1):
            row = heat[y]
            below = heat[y + 1]
            for x in range(width):
                src = min(last, max(0, x + random.choice(drift)))
                # take the source cell blurred with its neighbours: that keeps
                # the flame one coherent body with soft edges instead of
                # speckle, so the color really does follow the height
                value = (below[max(0, src - 1)] + 2 * below[src]
                         + below[min(last, src + 1)] + 2) // 4
                if value > SMOKE_MAX:
                    cooling = random.choice(decay) + edge_cooling[x] + extra_cooling
                else:
                    cooling = random.choice(smoke_decay)
                row[x] = min(MAX_HEAT, max(0, value - cooling))

    def display_fireplace(self, matrix):
        swap = self.get_canvas(matrix)
        opts = self.options
        geometry = None
        torches = heats = None

        for _ in range(int(opts['duration'] * opts['fps'])):
            frame_start = time.perf_counter()
            ember_scale = opts['embers'] / 100
            # flames maps to cooling: taller flames cool slower on the way up
            extra_cooling = 3 - int(opts['flames'])

            # rebuild the torches when spacing/height/size change, so those
            # sliders apply live like the other fire settings
            key = (int(opts['spacing']), int(opts['height']), int(opts['size']))
            if key != geometry:
                geometry = key
                torches = build_torches(*key)
                heats = [[[0] * torch.width for _ in range(torch.height)]
                         for torch in torches]

            swap.Clear()
            for torch, heat in zip(torches, heats):
                Fireplace.step_fire(heat, torch, ember_scale, extra_cooling)

                for x, y, (r, g, b) in torch.stick:
                    swap.SetPixel(x, y, r, g, b)

                # the fire grid's bottom row overlaps the head, so the
                # embers glow right on the wrap
                top = torch.tip_y - torch.height + 1
                for gy, row in enumerate(heat):
                    for gx, value in enumerate(row):
                        color = PALETTE[value]
                        if color:
                            swap.SetPixel(torch.left + gx, top + gy,
                                          color[0], color[1], color[2])

            swap = self.swap_canvas(matrix, swap)
            time.sleep(max(0.0, 1 / opts['fps'] - (time.perf_counter() - frame_start)))
