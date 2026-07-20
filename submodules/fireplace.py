import time
import random
from submodule import Submodule

# low heat is transparent (the black background shows), the hottest values are white
PALETTE = [
    None,
    None, None, (105, 22, 5), (135, 28, 6),
    (165, 38, 6), (190, 52, 8), (210, 68, 10), (225, 88, 12),
    (235, 108, 16), (243, 132, 20), (248, 158, 32), (252, 184, 48),
    (253, 208, 78), (254, 228, 120), (255, 246, 180),
]
MAX_HEAT = len(PALETTE) - 1

DECAY = (0, 0, 1, 1, 1, 1, 1, 2, 2, 3)  # avg 1.2 heat loss per row -> tall flames

# each torch runs its own small fire grid, centered over the torch head
FIRE_W = 13
_CENTER = (FIRE_W - 1) / 2

# bell seed: full heat over the torch head, nothing at the grid edges, so the
# flame starts as a fat tongue and only widens further by drifting upwards
SEED_MAX = []
EDGE_COOLING = []
for _x in range(FIRE_W):
    _d = abs(_x - _CENTER) / 4.0
    SEED_MAX.append(round(MAX_HEAT * max(0.0, 1 - _d * _d)))
    EDGE_COOLING.append(1 if _d > 1 else 0)

WOOD = (96, 56, 18)
WRAP = (156, 100, 36)   # the cloth-wrapped head the flame sits on


class _Torch:

    def __init__(self, base_x, tip_x, tip_y, fire_top, drift):
        self.tip_y = tip_y
        self.drift = drift
        self.height = tip_y - fire_top + 1
        self.left = tip_x - FIRE_W // 2

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
TORCHES = [
    _Torch(24, 21, 25, 8, (-1, 0, 0, 1, 1)),    # left, leaning outwards
    _Torch(31, 31, 23, 4, (-1, 0, 0, 0, 1)),    # center, upright and taller
    _Torch(38, 41, 25, 8, (-1, -1, 0, 0, 1)),   # right, leaning outwards
]


class Fireplace(Submodule):

    OPTIONS = {
        'priority': {'label': 'Priority', 'default': 4, 'min': 1.5, 'max': 10, 'step': 0.5},
        'embers':   {'label': 'Ember heat %', 'default': 100, 'min': 50, 'max': 100, 'step': 5},
        'flames':   {'label': 'Flame height', 'default': 3, 'min': 1, 'max': 4, 'step': 1},
        'duration': {'label': 'Duration s', 'default': 17, 'min': 5, 'max': 120, 'step': 1},
        'fps':      {'label': 'FPS', 'default': 15, 'min': 6, 'max': 30, 'step': 1},
    }

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)
        add_loop(self.options['priority'], self.display_fireplace)

    @staticmethod
    def step_fire(heat, drift, ember_scale, extra_cooling):
        # seed the bottom row (the torch head) with flickering heat
        height = len(heat)
        for x in range(FIRE_W):
            seed_max = round(SEED_MAX[x] * ember_scale)
            heat[height - 1][x] = random.randint(max(0, seed_max - 4), seed_max)

        # classic doom fire: heat rises, drifts sideways and cools down
        for y in range(height - 1):
            for x in range(FIRE_W):
                src = min(FIRE_W - 1, max(0, x + random.choice(drift)))
                cooling = random.choice(DECAY) + EDGE_COOLING[x] + extra_cooling
                heat[y][x] = min(MAX_HEAT, max(0, heat[y + 1][src] - cooling))

    def display_fireplace(self, matrix):
        swap = self.get_canvas(matrix)
        opts = self.options
        heats = [[[0] * FIRE_W for _ in range(torch.height)] for torch in TORCHES]

        for _ in range(int(opts['duration'] * opts['fps'])):
            frame_start = time.perf_counter()
            ember_scale = opts['embers'] / 100
            # flames maps to cooling: taller flames cool slower on the way up
            extra_cooling = 3 - int(opts['flames'])

            swap.Clear()
            for torch, heat in zip(TORCHES, heats):
                Fireplace.step_fire(heat, torch.drift, ember_scale, extra_cooling)

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
