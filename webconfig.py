#!/usr/bin/env python3
"""Web interface for switching ledstation modules on and off and tuning
their settings.

Runs as its own process (scheduler.py starts it automatically, or run it
standalone with `python3 webconfig.py`). It only ever reads and writes
modules.conf - the scheduler watches that file and applies changes
between module runs, so this server never talks to the display process.
The option specs (ranges, labels) come from modules_meta.json, which the
scheduler writes on startup.
"""
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import module_config
import settings

log = logging.getLogger(__name__)

WEBUI_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webui.html')


def read_meta():
    try:
        with open(settings.MODULES_META) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def read_conf():
    try:
        return module_config.read(settings.MODULES_CONF)
    except Exception:
        return {}, {}


def module_list():
    enabled, options = read_conf()
    meta = read_meta()

    result = []
    for name in sorted(enabled):
        entry = {'name': name, 'enabled': enabled[name], 'options': []}
        values = module_config.merge_options(meta.get(name, {}), options.get(name, {}))
        for key, spec in meta.get(name, {}).items():
            entry['options'].append({
                'key': key,
                'label': spec.get('label', key),
                'min': spec['min'], 'max': spec['max'],
                'step': spec['step'], 'default': spec['default'],
                'value': values[key],
            })
        result.append(entry)
    return result


class Handler(BaseHTTPRequestHandler):

    def _respond(self, status, body, content_type):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _respond_json(self, status, payload):
        self._respond(status, json.dumps(payload).encode(), 'application/json')

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length))

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            with open(WEBUI_PATH, 'rb') as f:
                self._respond(200, f.read(), 'text/html; charset=utf-8')
        elif self.path == '/api/modules':
            self._respond_json(200, {'modules': module_list()})
        else:
            self._respond_json(404, {'error': 'not found'})

    def do_POST(self):
        if self.path == '/api/toggle':
            self._handle_toggle()
        elif self.path == '/api/option':
            self._handle_option()
        else:
            self._respond_json(404, {'error': 'not found'})

    def _handle_toggle(self):
        try:
            data = self._read_body()
            name = data['name']
            wanted = bool(data['enabled'])
        except (ValueError, KeyError, TypeError):
            self._respond_json(400, {'error': 'invalid request'})
            return

        enabled, options = read_conf()
        if name not in enabled:
            self._respond_json(404, {'error': 'unknown module'})
            return

        enabled[name] = wanted
        module_config.write(settings.MODULES_CONF, enabled, options)
        log.info("%s -> %s", name, 'on' if wanted else 'off')
        self._respond_json(200, {'modules': module_list()})

    def _handle_option(self):
        try:
            data = self._read_body()
            name = data['module']
            key = data['key']
            value = float(data['value'])
        except (ValueError, KeyError, TypeError):
            self._respond_json(400, {'error': 'invalid request'})
            return

        meta = read_meta()
        spec = meta.get(name, {}).get(key)
        if spec is None:
            self._respond_json(404, {'error': 'unknown option'})
            return

        enabled, options = read_conf()
        values = module_config.merge_options(meta[name], options.get(name, {}))
        values[key] = min(spec['max'], max(spec['min'], value))
        options[name] = values
        module_config.write(settings.MODULES_CONF, enabled, options)
        log.info("%s.%s -> %s", name, key, module_config.format_value(values[key]))
        self._respond_json(200, {'modules': module_list()})

    def log_message(self, format, *args):
        pass  # request noise is not interesting, real events are logged above


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s [webconfig] %(message)s")
    server = ThreadingHTTPServer(('', settings.WEB_UI_PORT), Handler)
    log.info("Serving module config UI on port %d", settings.WEB_UI_PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
