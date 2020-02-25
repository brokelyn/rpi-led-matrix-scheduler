from init import init_leds
import queue
import threading

import inspect
import sys
import types
from subtasks import *
from q_object import QObject


class Scheduler:

    def __init__(self):
        self.loop_q = queue.PriorityQueue()
        self.event_q = queue.PriorityQueue()
        self.event_id = 1

        self.submodules = Scheduler.load_submodules()
        self.init_submodules()

        self.services = self.init_submodule_services()
        print("Done loading! " + str(len(self.services)) + " services are runnning.\n")

        self.matrix = init_leds()

        self.schedule()

    def get_id(self):
        self.event_id += 1
        return self.event_id

    def schedule(self):
        while True:
            self.next()

    def next(self):
        if not self.event_q.empty():
            event = self.event_q.get()
            print("Next: " + str(event.call_fnc))
            self.run_module(event.get_fnc())
        else:
            for obj in self.loop_q.queue:
                obj.adjust_prio()
            loop = self.loop_q.get()
            print("Next: " + str(loop.call_fnc))
            self.run_module(loop.get_fnc())
            self.loop_q.put(loop)

    def run_module(self, fnc):
        thread = threading.Thread(target=fnc, args=(self.matrix, ))
        thread.start()
        thread.join()

    @staticmethod
    def load_submodules():
        classes = []
        for name, val in globals().items():
            if isinstance(val, types.ModuleType) and "subtasks" in val.__name__:
                print("Found submodule %s" % val)
                clsmembers = inspect.getmembers(val, inspect.isclass)
                classes.append(clsmembers[0][1]())
        return classes

    def init_submodules(self):
        for mod in self.submodules:
            try:
                mod.init(self.add_loop)
            except AttributeError:
                print("Could not load: " + str(mod) + ". Missing 'init' method", file=sys.stderr)

    def init_submodule_services(self):
        services = []
        for mod in self.submodules:
            try:
                thread = threading.Thread(target=mod.service, args=(self.add_event, ))
                thread.start()
                services.append(thread)
            except AttributeError:
                print("Module: " + str(mod) + " has no 'service' method.", file=sys.stderr)
        return services

    def add_event(self, priority, display_fnc):  # todo return id
        qObj = QObject(priority, self.get_id(), display_fnc)
        self.event_q.put(qObj)

    def add_loop(self, priority, display_fnc):
        qObj = QObject(priority, self.get_id(), display_fnc)
        self.loop_q.put(qObj)


Scheduler()
