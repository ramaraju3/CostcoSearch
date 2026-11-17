#!/usr/bin/env python3
"""Serve ONE file -- the trimmed costco.db -- to the search page on GitHub Pages.

Runs on the Pi, bound to localhost only; `tailscale serve` puts HTTPS in front
of it, so only devices on your tailnet can reach it. Nothing else in the folder
is ever served.

    serve_db.py --file /home/nani/costco/data/costco.db --port 8790 \
        --origin https://ramaraju3.github.io
"""
import argparse
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def make_handler(path, origins):
    class Handler(BaseHTTPRequestHandler):
        server_version = "costco-db/1"
        sys_version = ""

        def _cors(self):
            origin = self.headers.get("Origin")
            if origin in origins:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
                self.send_header("Access-Control-Expose-Headers", "Last-Modified, Content-Length")
                # Chrome's Private Network Access: a public site asking a private address.
                if self.headers.get("Access-Control-Request-Private-Network") == "true":
                    self.send_header("Access-Control-Allow-Private-Network", "true")

        def do_OPTIONS(self):
            self.send_response(204)
            self._cors()
            self.send_header("Access-Control-Allow-Methods", "GET, HEAD")
            self.send_header("Access-Control-Max-Age", "600")
            self.end_headers()

        def do_HEAD(self):
            self._serve(body=False)

        def do_GET(self):
            self._serve(body=True)

        def _serve(self, body):
            if self.path.split("?")[0] not in ("/costco.db", "/"):
                self.send_error(404)
                return
            try:
                with open(path, "rb") as f:
                    data = f.read()
                    mtime = os.fstat(f.fileno()).st_mtime
            except FileNotFoundError:
                self.send_error(404, "No database yet; run a sync on the Mac")
                return
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/vnd.sqlite3")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Last-Modified", self.date_time_string(mtime))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if body:
                self.wfile.write(data)

        def log_message(self, fmt, *args):  # one short line per request, no headers
            print(f"{self.address_string()} {fmt % args}", flush=True)

    return Handler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--port", type=int, default=8790)
    ap.add_argument("--bind", default="127.0.0.1")
    ap.add_argument("--origin", action="append", required=True, help="allowed page origin; repeatable")
    a = ap.parse_args()
    ThreadingHTTPServer((a.bind, a.port), make_handler(a.file, set(a.origin))).serve_forever()


if __name__ == "__main__":
    main()
