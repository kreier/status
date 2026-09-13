"""Status page web application and API service.

Serves the host status dashboard and JSON API.
Compatible with direct access (e.g. http://rk3229/status)
and reverse proxies like Traefik (https://rk3229.hv.io.vn/status/).
"""

import json
import os
import sys

from core import host_info

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

try:
    from flask import Flask, jsonify, request, send_from_directory

    app = Flask(__name__, static_folder=None)

    @app.route("/")
    @app.route("/status")
    @app.route("/status/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.route("/<path:filename>")
    @app.route("/status/<path:filename>")
    def static_files(filename):
        # Prevent accessing API routes as static files
        if filename.startswith("api"):
            return jsonify({"error": "Not found"}), 404
        return send_from_directory(FRONTEND_DIR, filename)

    @app.route("/api", methods=["GET"])
    @app.route("/api/status", methods=["GET"])
    @app.route("/status/api", methods=["GET"])
    @app.route("/status/api/status", methods=["GET"])
    def get_status():
        return jsonify(host_info.get_all_status())

    @app.route("/api/check", methods=["POST"])
    @app.route("/status/api/check", methods=["POST"])
    def check_updates():
        res = host_info.check_updates()
        # Return full current status alongside check info
        data = host_info.get_all_status()
        data["updates"] = res
        return jsonify(data)

    @app.route("/api/update", methods=["POST"])
    @app.route("/status/api/update", methods=["POST"])
    def trigger_update():
        res = host_info.trigger_update()
        return jsonify(res)

    def run():
        port = int(os.environ.get("PORT", 8000))
        host = os.environ.get("HOST", "0.0.0.0")
        app.run(host=host, port=port)

except ImportError:
    # Fallback to Python standard library http.server if Flask is not yet installed
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    from urllib.parse import urlparse

    class StatusRequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

        def _send_json(self, data, status_code=200):
            payload = json.dumps(data).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/")

            if path in ("", "/status"):
                self.path = "/index.html"
                return super().do_GET()
            elif path in ("/api", "/api/status", "/status/api", "/status/api/status"):
                self._send_json(host_info.get_all_status())
                return
            elif path.startswith("/status/"):
                # Strip /status prefix for static assets
                self.path = self.path[len("/status"):]
                return super().do_GET()
            else:
                return super().do_GET()

        def do_POST(self):
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/")

            if path in ("/api/check", "/status/api/check"):
                res = host_info.check_updates()
                data = host_info.get_all_status()
                data["updates"] = res
                self._send_json(data)
            elif path in ("/api/update", "/status/api/update"):
                res = host_info.trigger_update()
                self._send_json(res)
            else:
                self._send_json({"error": "Not found"}, 404)

    app = None

    def run():
        port = int(os.environ.get("PORT", 8000))
        host = os.environ.get("HOST", "0.0.0.0")
        server = HTTPServer((host, port), StatusRequestHandler)
        print(f"Serving status page on http://{host}:{port}/status (fallback standard library)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    run()
