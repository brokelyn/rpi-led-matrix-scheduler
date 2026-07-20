import time
import random
from PIL import Image
from submodule import Submodule
import settings

# The hearth opening of the background image: display row y -> (x0, x1) inclusive.
# Everything inside is animated fire, everything outside stays static background.
FIRE_ROWS = {11: (24, 35), 12: (22, 37)}
for _y in range(13, 22):
    FIRE_ROWS[_y] = (21, 38)

FIRE_TOP = min(FIRE_ROWS)
FIRE_LEFT = min(x0 for x0, _ in FIRE_ROWS.values())
FIRE_WIDTH = max(x1 for _, x1 in FIRE_ROWS.values()) - FIRE_LEFT + 1
FIRE_HEIGHT = max(FIRE_ROWS) - FIRE_TOP + 1

# low heat is transparent (the dark hearth shows), the hottest values are white
PALETTE = [
    None,
    None, None, (105, 22, 5), (135, 28, 6),
    (165, 38, 6), (190, 52, 8), (210, 68, 10), (225, 88, 12),
    (235, 108, 16), (243, 132, 20), (248, 158, 32), (252, 184, 48),
    (253, 208, 78), (254, 228, 120), (255, 246, 180),
]
MAX_HEAT = len(PALETTE) - 1

DECAY = (0, 1, 1, 2, 2, 2, 2, 2, 2, 3)  # avg 1.7 heat loss per row keeps flames below the arch
DRIFT = (-1, 0, 0, 0, 1)

# bell-shaped ember bed: full heat in the middle of the hearth, low at the edges
_CENTER = (FIRE_WIDTH - 1) / 2
SEED_MAX = []
EDGE_COOLING = []
for _x in range(FIRE_WIDTH):
    _d = abs(_x - _CENTER) / _CENTER
    SEED_MAX.append(round(MAX_HEAT * (0.3 + 0.7 * (1 - _d * _d))))
    EDGE_COOLING.append(1 if _d > 0.7 else 0)


class Fireplace(Submodule):

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)

        # a missing image fails initialisation, the scheduler then skips this module
        image = Image.open(settings.IMAGES_PATH + 'fireplace.png')
        if image.size != (64, 32):
            image = image.resize((64, 32))
        self.background = image.convert('RGB')

        add_loop(4, self.display_fireplace)

    @staticmethod
    def step_fire(heat):
        # seed the bottom row (the embers) with flickering, center-weighted heat
        for x in range(FIRE_WIDTH):
            heat[FIRE_HEIGHT - 1][x] = random.randint(max(0, SEED_MAX[x] - 4), SEED_MAX[x])

        # classic doom fire: heat rises, drifts sideways and cools down
        for y in range(FIRE_HEIGHT - 1):
            for x in range(FIRE_WIDTH):
                src = min(FIRE_WIDTH - 1, max(0, x + random.choice(DRIFT)))
                cooling = random.choice(DECAY) + EDGE_COOLING[x]
                heat[y][x] = max(0, heat[y + 1][src] - cooling)

    def display_fireplace(self, matrix):
        swap = matrix.CreateFrameCanvas()
        heat = [[0] * FIRE_WIDTH for _ in range(FIRE_HEIGHT)]

        for _ in range(260):  # ~17 seconds, the fire "catches" from the embers
            Fireplace.step_fire(heat)

            swap.SetImage(self.background, 0, 0, unsafe=False)

            for y, (x0, x1) in FIRE_ROWS.items():
                row = heat[y - FIRE_TOP]
                for x in range(x0, x1 + 1):
                    color = PALETTE[row[x - FIRE_LEFT]]
                    if color:
                        swap.SetPixel(x, y, color[0], color[1], color[2])

            swap = matrix.SwapOnVSync(swap)
            time.sleep(0.065)
