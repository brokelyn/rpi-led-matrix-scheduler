import math
import time
import random as rnd
from submodule import Submodule
from rgbmatrix import graphics


visual_range = 3
centering_factor = 0.008
avoid_factor = 0.08
matching_factor = 0.25
speed_limit = 1.1

height = 32
width = 64

visual_range_sq = visual_range ** 2
avoid_range_sq = 2 ** 2


class point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class body:
    def __init__(self, location, velocity, color=graphics.Color(200, 0, 0)):
        self.location = location
        self.velocity = velocity
        self.color = color


def apply_flocking(bodies):
    # one pass over all pairs replaces the former flyTowardsCenter,
    # avoidOthers and matchVelocity loops: one squared-distance check
    # per pair instead of three sqrt calls
    for body in bodies:
        center_x = center_y = 0.0
        center_n = 0
        dodge_x = dodge_y = 0.0
        match_x = match_y = 0.0
        match_n = 0

        for other in bodies:
            dx = other.location.x - body.location.x
            dy = other.location.y - body.location.y
            dist_sq = dx * dx + dy * dy

            if dist_sq < visual_range_sq:
                center_x += other.location.x
                center_y += other.location.y
                center_n += 1

            if other is body:
                continue

            if dist_sq < avoid_range_sq:
                dodge_x -= dx
                dodge_y -= dy

            if dist_sq < visual_range_sq:
                match_x += other.velocity.x
                match_y += other.velocity.y
                match_n += 1

        if center_n > 0:
            body.velocity.x += (center_x / center_n - body.location.x) * centering_factor
            body.velocity.y += (center_y / center_n - body.location.y) * centering_factor

        body.velocity.x += dodge_x * avoid_factor
        body.velocity.y += dodge_y * avoid_factor

        if match_n > 0:
            body.velocity.x += (match_x / match_n - body.velocity.x) * matching_factor
            body.velocity.y += (match_y / match_n - body.velocity.y) * matching_factor


def limitSpeed(bodies):
    for body in bodies:
        body.velocity.x = body.velocity.x * 1.025
        body.velocity.y = body.velocity.y * 1.025

        speed = math.sqrt(body.velocity.x ** 2 + body.velocity.y ** 2)
        if speed > speed_limit:
            body.velocity.x = (body.velocity.x / speed) * speed_limit
            body.velocity.y = (body.velocity.y / speed) * speed_limit


def keepWithinBounds(bodies):
    for body in bodies:
        margin = 4
        turnFactor = 0.3

        if body.location.x < margin:
            body.velocity.x += turnFactor
        if body.location.x > width - margin:
            body.velocity.x -= turnFactor
        if body.location.y < margin:
            body.velocity.y += turnFactor
        if body.location.y > height - margin:
            body.velocity.y -= turnFactor


def colorBySpeed(bodies):
    color_step_size = 255 / speed_limit

    for body in bodies:
        red = min(255, int(color_step_size * abs(body.velocity.x)) + 20)
        blue = min(255, int(color_step_size * abs(body.velocity.y)) + 20)
        green = 20

        body.color = graphics.Color(red, green, blue)


def update_location(bodies):
    for target_body in bodies:
        target_body.location.x += target_body.velocity.x
        target_body.location.y += target_body.velocity.y


def compute_step(bodies):
    apply_flocking(bodies)
    limitSpeed(bodies)
    keepWithinBounds(bodies)

    colorBySpeed(bodies)

    update_location(bodies)


def rnd_point(minx, maxx, miny, maxy):
    return point(rnd.random() * (maxx - minx) + minx, rnd.random() * (maxy - miny) + miny)


class Boids(Submodule):

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)
        add_loop(4.5, self.display_swarm)

    def display_swarm(self, matrix):
        swap = self.get_canvas(matrix)

        bodies = [body(rnd_point(1, 63, 1, 31), rnd_point(-1, 0, -1, 0)) for _ in range(25)]

        frame_time = 0.015
        for _ in range(650):
            frame_start = time.perf_counter()
            compute_step(bodies)

            swap.Clear()
            for obj in bodies:
                swap.SetPixel(obj.location.x, obj.location.y, obj.color.red, obj.color.green, obj.color.blue)

            swap = self.swap_canvas(matrix, swap)
            # sleep only the remainder of the frame budget so system load
            # doesn't slow the animation down
            time.sleep(max(0.0, frame_time - (time.perf_counter() - frame_start)))
