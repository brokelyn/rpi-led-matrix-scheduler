from init import init_leds
import itertools
import logging
import threading
import time

import inspect
import types
import settings
from submodule import Submodule
from submodules import *

log = logging.getLogger(__name__)


class QObject:

    def __init__(self, priority, id, fnc):
        self.base_prio = priority
        self.curr_prio = priority
        self.call_fnc = fnc

        self.id = id

    def adjust_prio(self):
        self.curr_prio = max(1.1, self.curr_prio - 0.2)


class Scheduler:

    def __init__(self):
        # one lock guards both lists; add_event/add_loop/rmv_loop are called
        # from service threads while the scheduler thread picks the next item
        self._lock = threading.Lock()
        self._id_counter = itertools.count(1)
        self.loops = []
        self.events = []

        self.submodules = self.load_submodules()
        settings.LOADED_MODULES = len(self.submodules)
        log.info("Done loading modules! %d modules were loaded.", len(self.submodules))

        self.services = self.init_submodule_services()
        settings.RUNNING_SERVICES = len(self.services)
        log.info("Done loading services! %d services are running.", len(self.services))

        self.matrix = init_leds()

    def schedule(self):
        while True:
            self.next()

    def next(self):
        with self._lock:
            if self.events:
                item = min(self.events, key=lambda obj: obj.curr_prio)
                self.events.remove(item)
                kind = "Event"
            elif self.loops:
                for obj in self.loops:
                    obj.adjust_prio()
                item = min(self.loops, key=lambda obj: obj.curr_prio)
                item.curr_prio = item.base_prio
                kind = "Loop"
            else:
                item = None

        if item is None:
            time.sleep(0.1)
            return

        log.info("%s next: %s", kind, item.call_fnc)
        self.run_module(item.call_fnc)

    def run_module(self, fnc):
        try:
            fnc(self.matrix)
        except Exception:
            log.exception("Module function %s crashed", fnc)

    def load_submodules(self):
        instances = []
        for name, val in globals().items():
            if isinstance(val, types.ModuleType) and "submodules" in val.__name__:
                log.info("Found submodule %s", val.__name__)
                for _, cls in inspect.getmembers(val, inspect.isclass):
                    if not (issubclass(cls, Submodule) and cls is not Submodule
                            and cls.__module__ == val.__name__):
                        continue
                    try:
                        instances.append(cls(self.add_loop, self.rmv_loop, self.add_event))
                    except Exception:
                        log.exception("Failed to initialise module %s - skipping it", cls.__name__)
        return instances

    def init_submodule_services(self):
        services = []
        for mod in self.submodules:
            service = getattr(mod, "service", None)
            if not callable(service):
                continue
            thread = threading.Thread(target=service, daemon=True,
                                      name=type(mod).__name__ + "-service")
            thread.start()
            services.append(thread)
            log.info("Loaded service of module: %s", type(mod).__name__)
        return services

    def add_event(self, priority, display_fnc):
        return self._add(self.events, priority, display_fnc)

    def add_loop(self, priority, display_fnc):
        return self._add(self.loops, priority, display_fnc)

    def _add(self, queue, priority, display_fnc):
        id = next(self._id_counter)
        with self._lock:
            queue.append(QObject(priority, id, display_fnc))
        return id

    def rmv_loop(self, id):
        with self._lock:
            for obj in self.loops:
                if obj.id == id:
                    self.loops.remove(obj)
                    return
        raise LookupError("Can't find ID for loop function!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s [%(threadName)s] %(message)s")
    scheduler = Scheduler()
    try:
        scheduler.schedule()
    except KeyboardInterrupt:
        scheduler.matrix.Clear()
        log.info("Shutting down.")
