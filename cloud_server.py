"""Read-only ReviewLab preview: saved responses and deterministic rule evaluation.

No model execution, credentials, historical datasets or arbitrary file routes.
"""
import argparse
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import parse_qs, urlparse

import selection_core
from public_view import reader_materials, reader_status

ROOT = Path(__file__).resolve().parent
COMPUTE = threading.BoundedSemaphore(2)
FILES = {
    '/': ('web/panel.html', 'text/html; charset=utf-8'),
    '/panel.css': ('web/panel.css', 'text/css; charset=utf-8'),
    '/panel.js': ('web/panel.js', 'text/javascript; charset=utf-8'),
    '/proposal.docx': ('proposal.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
    '/appendix.docx': ('appendix.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
    '/applications.docx': ('applications.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
}


def encode(value):
    return json.dumps(value, ensure_ascii=False).encode('utf-8')


@lru_cache(maxsize=128)
def evaluated(budget, threshold, joint):
    return encode(selection_core.evaluate(budget, threshold, joint))


class Handler(BaseHTTPRequestHandler):
    server_version = 'ReviewLab'
    sys_version = ''

    def log_message(self, fmt, *args):
        pass

    def send(self, data, kind='application/json; charset=utf-8', status=200):
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'self'")
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(data)

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        self.send(encode({'message': 'API execution is disabled in the shared preview.'}), status=405)

    def do_GET(self):
        path = urlparse(self.path)
        try:
            if path.path in FILES:
                filename, kind = FILES[path.path]
                self.send((ROOT / filename).read_bytes(), kind)
            elif path.path == '/api/panel/materials':
                self.send(encode(reader_materials(selection_core.materials())))
            elif path.path == '/api/panel/design':
                self.send(encode(selection_core.design()))
            elif path.path == '/api/panel/results':
                self.send(encode(reader_status(selection_core.status())))
            elif path.path == '/api/panel/evaluate':
                args = parse_qs(path.query, keep_blank_values=True)
                if set(args) - {'budget', 'threshold', 'joint'} or any(len(v) != 1 for v in args.values()):
                    raise ValueError('Invalid parameters')
                budget = int(args.get('budget', ['3'])[0])
                threshold = float(args.get('threshold', ['70'])[0])
                joint = args.get('joint', ['0'])[0]
                if not 1 <= budget <= 9 or not 0 <= threshold <= 100 or joint not in {'0', '1'}:
                    raise ValueError('Invalid parameters')
                if not COMPUTE.acquire(blocking=False):
                    self.send(encode({'message': 'The evaluator is busy. Please retry shortly.'}), status=429)
                    return
                try:
                    self.send(evaluated(budget, threshold, joint == '1'))
                finally:
                    COMPUTE.release()
            elif path.path == '/health':
                self.send(encode({'status': 'ok', 'application': 'ReviewLab', 'mode': 'saved_run_only', 'release': 'github-artifact-v1'}))
            else:
                self.send(encode({'message': 'Resource not found.'}), status=404)
        except (ValueError, TypeError):
            self.send(encode({'message': 'Invalid selection parameters.'}), status=400)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self.send(encode({'message': 'The preview could not complete this request.'}), status=500)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bind', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=3006)
    options = parser.parse_args()
    ThreadingHTTPServer((options.bind, options.port), Handler).serve_forever()
