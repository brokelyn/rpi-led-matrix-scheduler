import math
import time
import random as rnd
from submodule import Submodule
from rgbmatrix import graphics


class point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class body:
    def __init__(self, location, mass, velocity, name="", color=graphics.Color(200, 0, 0), is_fix=False):
        self.location = location
        self.mass = mass
        self.velocity = velocity
        self.name = name
        self.color = color
        self.is_fix = is_fix
        self.his = []


def calculate_single_body_acceleration(bodies, body_index):
    acceleration = point(0, 0)
    target_body = bodies[body_index]
    for index, external_body in enumerate(bodies):
        if index != body_index:
            r = (target_body.location.x - external_body.location.x) ** 2 +\
                (target_body.location.y - external_body.location.y) ** 2
            r = math.sqrt(r)
            tmp = external_body.mass / r ** 3
            acceleration.x += tmp * (external_body.location.x - target_body.location.x) * (r / 20)  # more speed
            acceleration.y += tmp * (external_body.location.y - target_body.location.y) * (r / 20)  # when far away

    return acceleration


def compute_velocity(bodies, time_step=1):
    for body_index, target_body in enumerate(bodies):
        acceleration = calculate_single_body_acceleration(bodies, body_index)
        target_body.velocity.x *= 0.99 * time_step  # like air
        target_body.velocity.y *= 0.99 * time_step  # resistance
        target_body.velocity.x += acceleration.x * time_step
        target_body.velocity.y += acceleration.y * time_step


def update_location(bodies, time_step = 1):
    for target_body in bodies:
        if not target_body.is_fix:
            target_body.his.append(point(target_body.location.x, target_body.location.y))  # just for tail
            if len(target_body.his) > 16:
                target_body.his = target_body.his[1:]
            target_body.location.x += target_body.velocity.x * time_step
            target_body.location.y += target_body.velocity.y * time_step


def compute_gravity_step(bodies, time_step = 1):
    compute_velocity(bodies, time_step = time_step)
    update_location(bodies, time_step = time_step)


def rnd_point(minx, maxx, miny, maxy):
    return point(rnd.random() * (maxx - minx) + minx, rnd.random() * (maxy - miny) + miny)


class Galaxy(Submodule):

    def __init__(self, add_loop, rmv_loop, add_event):
        super().__init__(add_loop, rmv_loop, add_event)
        add_loop(4, self.display_galaxy)

    def display_galaxy(self, matrix):
        swap = matrix.CreateFrameCanvas()
        body_mass = rnd.random()
        sun_mass = rnd.random() * 2 + 1

        # build list of planets in the simulation, or create your own
        bodies = [
            body(location=point(32, 10), mass=body_mass, velocity=rnd_point(0, 0.1, 0, 0.1), name="blue",
                 color=graphics.Color(0, 0, 255)),
            body(location=point(25, 15), mass=body_mass, velocity=rnd_point(0, 0.1, 0, 0.1), name="green",
                 color=graphics.Color(0, 255, 0)),
            body(location=point(10, 15), mass=body_mass, velocity=rnd_point(0, 0.1, 0, 0.1), name="red",
                 color=graphics.Color(255, 0, 0)),
            body(location=point(55, 15), mass=body_mass, velocity=rnd_point(0, 0.1, 0, 0.1), name="purple",
                 color=graphics.Color(177, 52, 235)),
            body(location=point(10, 25), mass=body_mass, velocity=rnd_point(0, 0.1, 0, 0.1), name="orange",
                 color=graphics.Color(235, 159, 52)),
            body(location=point(44, 8), mass=sun_mass, velocity=point(0, 0), name="sun1",
                 color=graphics.Color(255, 170, 0), is_fix=True),
            body(location=point(20, 8), mass=sun_mass, velocity=point(0, 0), name="sun2",
                 color=graphics.Color(255, 170, 0), is_fix=True),
            body(location=point(31, 24), mass=sun_mass, velocity=point(0, 0), name="sun3",
                 color=graphics.Color(255, 170, 0), is_fix=True)

        ]

        for i in range(800):
            compute_gravity_step(bodies, time_step=1)
            swap.Clear()

            for obj in bodies:
                swap.SetPixel(obj.location.x, obj.location.y, obj.color.red, obj.color.green, obj.color.blue)
                for i, his in enumerate(reversed(obj.his)):
                    reduce_step = 255 / len(obj.his)
                    r = max(0, obj.color.red - (i * reduce_step))
                    g = max(0, obj.color.green - (i * reduce_step))
                    b = max(0, obj.color.blue - (i * reduce_step))
                    swap.SetPixel(his.x, his.y, r, g, b)

            matrix.SwapOnVSync(swap)
            time.sleep(0.02)
