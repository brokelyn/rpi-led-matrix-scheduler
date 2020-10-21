from init import init_leds
import queue
import threading

import inspect
import types
import random
import settings
from subtasks import *
from q_object import QObject


class Scheduler:

    def __init__(self):
        self.loop_q = queue.PriorityQueue()
        self.event_q = queue.PriorityQueue()

        self.submodules = self.load_submodules()
        settings.LOADED_MODULES = len(self.submodules)
        print("Done loading Modules! " + str(len(self.submodules)) + " modules were loaded.\n")
        self.services = self.init_submodule_services()
        settings.RUNNING_SERVICES = len(self.services)
        print("Done loading Services! " + str(len(self.services)) + " services are runnning.\n")

        self.matrix = init_leds()

        self.schedule()

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
            fnc = loop.get_fnc()
            self.loop_q.put(loop)

            print("Next: " + str(loop.call_fnc))
            self.run_module(fnc)

    def run_module(self, fnc):
        thread = threading.Thread(target=fnc, args=(self.matrix, ))
        thread.start()
        thread.join()

    def load_submodules(self):
        classes = []
        for name, val in globals().items():
            if isinstance(val, types.ModuleType) and "subtasks" in val.__name__:
                print("Found submodule %s" % val)
                clsmembers = inspect.getmembers(val, inspect.isclass)
                classes.append(clsmembers[0][1](self.add_loop, self.rmv_loop, self.add_event))
        return classes

    def init_submodule_services(self):
        services = []
        for mod in self.submodules:
            try:
                thread = threading.Thread(target=mod.service, args=())
                thread.start()
                services.append(thread)
                print("Loaded Service of module: " + str(mod))
            except AttributeError:
                pass
                #print("Module: " + str(mod) + " has no 'service' method.", file=sys.stderr)
        return services

    def add_event(self, priority, display_fnc):
        id = random.getrandbits(128)
        qObj = QObject(priority, id, display_fnc)
        self.event_q.put(qObj)
        return id

    def add_loop(self, priority, display_fnc):
        id = random.getrandbits(128)
        qObj = QObject(priority, id, display_fnc)
        self.loop_q.put(qObj)
        return id

    def rmv_loop(self, id):
        for obj in self.loop_q.queue:
            if obj.id == id:
                self.loop_q.queue.remove(obj)
                return
        raise Exception("Cant find ID for loop function!")


if __name__ == "__main__":
    Scheduler()
