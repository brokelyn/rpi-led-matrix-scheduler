from init import init_leds
import itertools
import json
import logging
import os
import subprocess
import sys
import threading
import time

import inspect
import types
import module_config
import settings
from submodule import Submodule
from submodules import *

log = logging.getLogger(__name__)


class QObject:

    def __init__(self, priority, id, fnc, module=None):
        self.base_prio = priority
        self.curr_prio = priority
        self.call_fnc = fnc
        self.module = module

        self.id = id

    def adjust_prio(self):
        self.curr_prio = max(1.1, self.curr_prio - 0.2)


class Scheduler:

    def __init__(self):
        # one lock guards the queues, the enabled set and the loop
        # registrations; add_event/add_loop/rmv_loop are called from service
        # threads while the scheduler thread picks the next item
        self._lock = threading.Lock()
        self._id_counter = itertools.count(1)
        self.loops = []
        self.events = []

        self.instances = {}       # module name -> instance (once created)
        self.loop_regs = {}       # module name -> {loop id: (priority, fnc)}
        self.enabled = set()
        self.services = []

        self.module_classes = self.discover_submodules()
        self.option_specs = {name: getattr(cls, 'OPTIONS', {})
                             for name, cls in self.module_classes.items()}

        enabled_conf, self.module_options = module_config.ensure(
            settings.MODULES_CONF, self.option_specs)
        self._conf_mtime = self._conf_stat()
        self._last_meta = None
        self.apply_config(enabled_conf)  # also writes the meta file
        self._chown_to_sudo_user(settings.MODULES_CONF, settings.MODULES_META)

        settings.LOADED_MODULES = len(self.instances)
        log.info("Done loading modules! %d of %d modules are enabled.",
                 len(self.instances), len(self.module_classes))

        settings.RUNNING_SERVICES = len(self.services)
        log.info("Done loading services! %d services are running.", len(self.services))

        self.matrix = init_leds()

    def schedule(self):
        while True:
            self.check_config()
            self.check_show_request()
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

    # ---------------------------------------------------- module lifecycle

    def discover_submodules(self):
        classes = {}
        for name, val in globals().items():
            if isinstance(val, types.ModuleType) and "submodules" in val.__name__:
                log.info("Found submodule %s", val.__name__)
                for _, cls in inspect.getmembers(val, inspect.isclass):
                    if (issubclass(cls, Submodule) and cls is not Submodule
                            and cls.__module__ == val.__name__):
                        classes[cls.__name__] = cls
        return classes

    def apply_config(self, conf):
        for name in self.module_classes:
            if conf.get(name, True):
                self.enable_module(name)
            else:
                self.disable_module(name)
        # instantiating modules may have registered new loops, which
        # decides what the web interface may offer a "show now" button for
        self.write_meta()

    def enable_module(self, name):
        with self._lock:
            if name in self.enabled:
                return
            self.enabled.add(name)
            if name in self.instances:
                # the module already exists: put its loops back
                for id, (priority, fnc) in self.loop_regs.get(name, {}).items():
                    self.loops.append(QObject(priority, id, fnc, name))
                log.info("Enabled module %s", name)
                return
        self._instantiate(name)

    def disable_module(self, name):
        with self._lock:
            if name not in self.enabled:
                return
            self.enabled.discard(name)
            # loop_regs is kept so enable_module can restore the loops
            self.loops = [obj for obj in self.loops if obj.module != name]
            self.events = [obj for obj in self.events if obj.module != name]
        log.info("Disabled module %s", name)

    def _instantiate(self, name):
        cls = self.module_classes[name]

        def tagged(fnc):
            return lambda priority, display_fnc: fnc(priority, display_fnc, name)

        try:
            # options are handed over before __init__ runs (the module reads
            # e.g. its loop priority from them) and shared by reference, so
            # later config changes reach the instance without any plumbing
            instance = cls.__new__(cls)
            instance.options = self.module_options.setdefault(name, {})
            instance.__init__(tagged(self.add_loop), self.rmv_loop, tagged(self.add_event))
        except Exception:
            log.exception("Failed to initialise module %s - skipping it", name)
            with self._lock:
                self.enabled.discard(name)
            return

        self.instances[name] = instance
        log.info("Enabled module %s", name)

        service = getattr(instance, "service", None)
        if callable(service):
            thread = threading.Thread(target=service, daemon=True,
                                      name=name + "-service")
            thread.start()
            self.services.append(thread)
            log.info("Loaded service of module: %s", name)

    # ------------------------------------------------------- config file

    def _conf_stat(self):
        try:
            return os.path.getmtime(settings.MODULES_CONF)
        except OSError:
            return None

    def check_config(self):
        mtime = self._conf_stat()
        if mtime is None or mtime == self._conf_mtime:
            return
        self._conf_mtime = mtime
        try:
            enabled_conf, options_conf = module_config.read(settings.MODULES_CONF)
        except Exception:
            log.exception("Ignoring invalid modules.conf")
            return
        log.info("modules.conf changed - applying")
        self.apply_options(options_conf)
        self.apply_config(enabled_conf)

    def apply_options(self, options_conf):
        for name, spec in self.option_specs.items():
            if not spec:
                continue
            merged = module_config.merge_options(spec, options_conf.get(name, {}))
            current = self.module_options.setdefault(name, merged)
            if current is merged or merged == current:
                continue
            old_priority = current.get('priority')
            # in place, so instances holding this dict see the new values
            current.update(merged)
            if 'priority' in current and current['priority'] != old_priority:
                self._reprioritize(name, current['priority'])

    def _reprioritize(self, name, priority):
        with self._lock:
            for obj in self.loops:
                if obj.module == name:
                    obj.base_prio = priority
                    obj.curr_prio = priority
            regs = self.loop_regs.get(name, {})
            for id, (_, fnc) in list(regs.items()):
                regs[id] = (priority, fnc)

    def check_show_request(self):
        if not os.path.exists(settings.SHOW_REQUEST):
            return
        try:
            with open(settings.SHOW_REQUEST) as f:
                request = json.load(f)
        except (OSError, ValueError):
            request = {}
        try:
            os.remove(settings.SHOW_REQUEST)
        except OSError:
            log.exception("Could not remove %s", settings.SHOW_REQUEST)

        name = request.get('module') if isinstance(request, dict) else None
        try:
            age = time.time() - float(request.get('time'))
        except (TypeError, ValueError):
            age = None
        if name is None or age is None or age > 120:
            log.info("Ignoring stale/invalid show request: %s", request)
            return

        with self._lock:
            regs = self.loop_regs.get(name, {})
            if name not in self.enabled or not regs:
                log.info("Show request for %s ignored - disabled or nothing to display", name)
                return
            for _, fnc in regs.values():
                # priority 0 beats every regular event, so it runs next
                self.events.append(QObject(0, next(self._id_counter), fnc, name))
        log.info("Show request: %s displays next", name)

    def write_meta(self):
        with self._lock:
            showable = {name for name, regs in self.loop_regs.items() if regs}
        meta = {name: {'options': spec, 'showable': name in showable}
                for name, spec in self.option_specs.items()
                if spec or name in showable}
        if meta == self._last_meta:
            return
        self._last_meta = meta
        try:
            module_config.atomic_write(settings.MODULES_META, json.dumps(meta, indent=2))
        except OSError:
            log.exception("Could not write %s", settings.MODULES_META)

    def _chown_to_sudo_user(self, *paths):
        # the scheduler usually runs as root (gpio) but the web interface
        # runs as the sudo user; hand the files over so they stay editable
        if hasattr(os, 'geteuid') and os.geteuid() == 0 and os.environ.get('SUDO_UID'):
            uid = int(os.environ['SUDO_UID'])
            gid = int(os.environ.get('SUDO_GID', uid))
            for path in paths:
                try:
                    os.chown(path, uid, gid)
                except OSError:
                    log.exception("Could not chown %s", path)

    # ------------------------------------------------------------ queues

    def add_event(self, priority, display_fnc, module=None):
        return self._add(self.events, priority, display_fnc, module)

    def add_loop(self, priority, display_fnc, module=None):
        return self._add(self.loops, priority, display_fnc, module)

    def _add(self, queue, priority, display_fnc, module=None):
        id = next(self._id_counter)
        with self._lock:
            if module is not None and module not in self.enabled:
                return None  # registrations from disabled modules are dropped
            queue.append(QObject(priority, id, display_fnc, module))
            if module is not None and queue is self.loops:
                self.loop_regs.setdefault(module, {})[id] = (priority, display_fnc)
        return id

    def rmv_loop(self, id):
        with self._lock:
            for obj in self.loops:
                if obj.id == id:
                    self.loops.remove(obj)
                    if obj.module is not None:
                        self.loop_regs.get(obj.module, {}).pop(id, None)
                    return
            # the loop may only exist as a registration of a disabled module
            for regs in self.loop_regs.values():
                if id in regs:
                    del regs[id]
                    return
        raise LookupError("Can't find ID for loop function!")


def start_web_ui():
    if os.environ.get('LEDSTATION_NO_WEB'):
        return None

    cmd = [sys.executable,
           os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webconfig.py')]

    # started via sudo the web server has no reason to stay root
    preexec = None
    if hasattr(os, 'geteuid') and os.geteuid() == 0 and os.environ.get('SUDO_UID'):
        uid = int(os.environ['SUDO_UID'])
        gid = int(os.environ.get('SUDO_GID', uid))

        def preexec():
            os.setgid(gid)
            os.setuid(uid)

    try:
        proc = subprocess.Popen(cmd, preexec_fn=preexec)
    except OSError:
        log.exception("Could not start web interface - continuing without it")
        return None
    log.info("Web interface started on port %d (pid %d).", settings.WEB_UI_PORT, proc.pid)
    return proc


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s [%(threadName)s] %(message)s")
    scheduler = Scheduler()
    web_ui = start_web_ui()
    try:
        scheduler.schedule()
    except KeyboardInterrupt:
        scheduler.matrix.Clear()
        log.info("Shutting down.")
    finally:
        if web_ui:
            web_ui.terminate()
