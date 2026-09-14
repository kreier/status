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

    @app.route("/", strict_slashes=False)
    @app.route("/status", strict_slashes=False)
    @app.route("/status/", strict_slashes=False)
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.route("/api", methods=["GET"], strict_slashes=False)
    @app.route("/api/status", methods=["GET"], strict_slashes=False)
    @app.route("/status/api", methods=["GET"], strict_slashes=False)
    @app.route("/status/api/status", methods=["GET"], strict_slashes=False)
    def get_status():
        return jsonify(host_info.get_all_status())

    @app.route("/api/history", methods=["GET"], strict_slashes=False)
    @app.route("/status/api/history", methods=["GET"], strict_slashes=False)
    def get_history():
        year = request.args.get("year") or request.args.get("years")
        if year:
            return jsonify(host_info.get_uptime_history(year=year))
        try:
            days = int(request.args.get("days", 90))
        except (ValueError, TypeError):
            days = 90
        return jsonify(host_info.get_uptime_history(days=days))

    @app.route("/api/tuptime", methods=["GET"], strict_slashes=False)
    @app.route("/status/api/tuptime", methods=["GET"], strict_slashes=False)
    def get_tuptime_raw():
        return jsonify(host_info.get_tuptime_entries())

    @app.route("/api/check", methods=["POST"], strict_slashes=False)
    @app.route("/status/api/check", methods=["POST"], strict_slashes=False)
    def check_updates():
        res = host_info.check_updates()
        # Return full current status alongside check info
        data = host_info.get_all_status()
        data["updates"] = res
        return jsonify(data)

    @app.route("/api/update", methods=["POST"], strict_slashes=False)
    @app.route("/status/api/update", methods=["POST"], strict_slashes=False)
    def trigger_update():
        res = host_info.trigger_update()
        return jsonify(res)

    @app.route("/<path:filename>")
    @app.route("/status/<path:filename>")
    def static_files(filename):
        # If the requested filename is empty, "status", or "index.html", serve index.html
        if filename in ("", "status", "index.html"):
            return send_from_directory(FRONTEND_DIR, "index.html")
        # Prevent accessing API routes as static files
        if filename.startswith("api"):
            return jsonify({"error": "Not found"}), 404
        return send_from_directory(FRONTEND_DIR, filename)

    @app.after_request
    def add_cache_headers(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

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
            elif path in ("/api/history", "/status/api/history"):
                from urllib.parse import parse_qs
                qs = parse_qs(parsed.query)
                year = qs.get("year", [None])[0] or qs.get("years", [None])[0]
                if year:
                    self._send_json(host_info.get_uptime_history(year=year))
                    return
                days = 90
                if "days" in qs and qs["days"][0].isdigit():
                    days = int(qs["days"][0])
                self._send_json(host_info.get_uptime_history(days=days))
                return
            elif path in ("/api/tuptime", "/status/api/tuptime"):
                self._send_json(host_info.get_tuptime_entries())
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
