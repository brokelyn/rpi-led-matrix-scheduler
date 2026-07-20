#!/usr/bin/env python3
"""Web interface for switching ledstation modules on and off.

Runs as its own process (scheduler.py starts it automatically, or run it
standalone with `python3 webconfig.py`). It only ever reads and writes
modules.conf - the scheduler watches that file and applies changes
between module runs, so this server never talks to the display process.
"""
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import module_config
import settings

log = logging.getLogger(__name__)

WEBUI_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webui.html')


def read_modules():
    try:
        modules = module_config.read(settings.MODULES_CONF)
    except Exception:
        modules = {}
    return [{'name': name, 'enabled': enabled}
            for name, enabled in sorted(modules.items())]


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

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            with open(WEBUI_PATH, 'rb') as f:
                self._respond(200, f.read(), 'text/html; charset=utf-8')
        elif self.path == '/api/modules':
            self._respond_json(200, {'modules': read_modules()})
        else:
            self._respond_json(404, {'error': 'not found'})

    def do_POST(self):
        if self.path != '/api/toggle':
            self._respond_json(404, {'error': 'not found'})
            return

        try:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            name = data['name']
            enabled = bool(data['enabled'])
        except (ValueError, KeyError, TypeError):
            self._respond_json(400, {'error': 'invalid request'})
            return

        try:
            modules = module_config.read(settings.MODULES_CONF)
        except (OSError, ValueError):
            modules = {}

        if name not in modules:
            self._respond_json(404, {'error': 'unknown module'})
            return

        modules[name] = enabled
        module_config.write(settings.MODULES_CONF, modules)
        log.info("%s -> %s", name, 'on' if enabled else 'off')
        self._respond_json(200, {'modules': read_modules()})

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
