import math
import time
import random as rnd
from rgbmatrix import graphics


visual_range = 3
centering_factor = 0.008
avoid_factor = 0.08
matching_factor = 0.25
speed_limit = 1.1

group_diff = 0.5
group_colors = [graphics.Color(200, 0, 0), graphics.Color(0, 200, 0), graphics.Color(0, 0, 200),
               graphics.Color(200, 0, 200), graphics.Color(200, 200, 0), graphics.Color(0, 200, 200),
               graphics.Color(200, 200, 200), graphics.Color(200, 100, 100), graphics.Color(50, 200, 100)]

height = 32
width = 64


class point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class body:
    def __init__(self, location, velocity, color=graphics.Color(200, 0, 0)):
        self.location = location
        self.velocity = velocity
        self.color = color
        self.his = []


def point_distance(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def flyTowardsCenter(bodies):
    for body in bodies:
        number = 0
        center = point(0, 0)
        for other in bodies:
            if point_distance(body.location, other.location) < visual_range:
                center.x += other.location.x
                center.y += other.location.y
                number += 1
        if number > 0:
            center.x = center.x / number
            center.y = center.y / number

            body.velocity.x += (center.x - body.location.x) * centering_factor
            body.velocity.y += (center.y - body.location.y) * centering_factor


def avoidOthers(bodies):
    for body_index, body in enumerate(bodies):
        dodge = point(0, 0)
        for other in [x for i, x in enumerate(bodies) if i != body_index]:
            distance = point_distance(body.location, other.location)
            if 2 > distance:
                dodge.x -= (other.location.x - body.location.x)
                dodge.y -= (other.location.y - body.location.y)

        body.velocity.x += dodge.x * avoid_factor
        body.velocity.y += dodge.y * avoid_factor


def matchVelocity(bodies):
    for body_index, body in enumerate(bodies):
        match_v = point(0, 0)
        number = 0
        for other in [x for i, x in enumerate(bodies) if i != body_index]:
            if point_distance(body.location, other.location) < visual_range:
                match_v.x += other.velocity.x
                match_v.y += other.velocity.y
                number += 1
        if number > 0:
            match_v.x = match_v.x / number
            match_v.y = match_v.y / number

            body.velocity.x += (match_v.x - body.velocity.x) * matching_factor
            body.velocity.y += (match_v.y - body.velocity.y) * matching_factor


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


def detect_groups(bodies):
    bodies_copy = bodies[:]
    num_groups = 0
    while len(bodies_copy) > 0:
        body = bodies_copy.pop()
        body.color = group_colors[num_groups % len(group_colors)]
        for other in bodies_copy:
            if point_distance(body.location, other.location) < visual_range:
                if abs(other.velocity.x - body.velocity.x) < group_diff:
                    if abs(other.velocity.y - body.velocity.y) < group_diff:
                        other.color = group_colors[num_groups % len(group_colors)]
                        bodies_copy.remove(other)
        num_groups += 1


def update_location(bodies):
    for target_body in bodies:
        target_body.his.append(point(target_body.location.x, target_body.location.y))  # just for tail
        if len(target_body.his) > 16:
            target_body.his = target_body.his[1:]

        target_body.location.x += target_body.velocity.x
        target_body.location.y += target_body.velocity.y


def compute_step(bodies):
    flyTowardsCenter(bodies)
    avoidOthers(bodies)
    matchVelocity(bodies)
    limitSpeed(bodies)
    keepWithinBounds(bodies)

    #detect_groups(bodies)

    update_location(bodies)


def rnd_point(minx, maxx, miny, maxy):
    return point(rnd.random() * (maxx - minx) + minx, rnd.random() * (maxy - miny) + miny)


class Boids:

    def init(self, add_loop, rmv_loop):
        add_loop(4.5, self.display_swarm)

    def service(self, add_event):
        pass

    def display_swarm(self, matrix):
        swap = matrix.CreateFrameCanvas()

        bodies = []

        for _ in range(25):
            bodies.append(body(rnd_point(1, 63, 1, 31), rnd_point(-1, 0, -1, 0)))

        for i in range(5000):
            compute_step(bodies)
            swap.Clear()

            for obj in bodies:
                swap.SetPixel(obj.location.x, obj.location.y, obj.color.red, obj.color.green, obj.color.blue)

            matrix.SwapOnVSync(swap)
            time.sleep(0.001)










