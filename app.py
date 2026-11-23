"""
NetPulse - Web Network Scanner
Main Application Server (Pure Python Standard Library - Zero External Dependencies)

Provides:
- Embedded HTTP & REST API server
- Background multi-threaded network scanner
- JSON / CSV export capabilities
- Interactive web frontend with floating inspection cards
"""

import sys
import os
import json
import csv
import io
import mimetypes
import argparse
import webbrowser
import threading
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# Import scanner modules
from scanner import NetworkScanner

# Initialize global scanner instance
scanner_instance = NetworkScanner()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")


class NetworkScannerHandler(BaseHTTPRequestHandler):
    """Custom HTTP Request Handler serving Web UI and REST API."""

    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, filepath, content_type):
        new_var = filepath
        if not os.path.exists(new_var):
            self.send_error(404, "File Not Found")
            return
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Server error: {e}")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # 1. Main Page
        if path in ["/", "/index.html"]:
            html_path = os.path.join(TEMPLATES_DIR, "index.html")
            self._serve_file(html_path, "text/html; charset=utf-8")
            return

        # 2. Static Assets (/static/css/style.css, /static/js/app.js, etc.)
        if path.startswith("/static/"):
            rel_path = path[len("/static/") :]
            abs_path = os.path.join(STATIC_DIR, rel_path)
            # Security check: prevent path traversal
            if not os.path.abspath(abs_path).startswith(STATIC_DIR):
                self.send_error(403, "Access Denied")
                return
            ctype, _ = mimetypes.guess_type(abs_path)
            self._serve_file(abs_path, ctype or "application/octet-stream")
            return

        # 3. API: Status & Device List
        if path == "/api/status":
            self._send_json(scanner_instance.get_status())
            return

        # 4. API: Network Interfaces / Gateway info
        if path == "/api/interfaces":
            scanner_instance._detect_network_info()
            data = {
                "local_ip": scanner_instance.local_ip,
                "gateway_ip": scanner_instance.gateway_ip,
                "subnet": scanner_instance.subnet,
            }
            self._send_json(data)
            return

        # 5. API: Export Data (JSON or CSV)
        if path == "/api/export":
            fmt = query.get("format", ["json"])[0].lower()
            devices = scanner_instance.devices

            if fmt == "csv":
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow([
                    "IP Address", "MAC Address", "Vendor", "Hostname",
                    "Friendly Name", "Device Type", "Estimated OS",
                    "Gateway", "Latency (ms)", "Open Ports", "Status"
                ])
                for d in devices:
                    writer.writerow([
                        d.get("ip", ""),
                        d.get("mac", ""),
                        d.get("vendor", ""),
                        d.get("hostname", ""),
                        d.get("friendly_name", ""),
                        d.get("device_type", ""),
                        d.get("os_estimate", ""),
                        "Yes" if d.get("is_gateway") else "No",
                        d.get("latency_ms", ""),
                        ", ".join(str(p) for p in d.get("open_ports", [])),
                        d.get("status", "")
                    ])
                csv_bytes = output.getvalue().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="network_scan_report.csv"')
                self.send_header("Content-Length", str(len(csv_bytes)))
                self.end_headers()
                self.wfile.write(csv_bytes)
                return
            else:
                json_bytes = json.dumps(devices, indent=2).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="network_scan_report.json"')
                self.send_header("Content-Length", str(len(json_bytes)))
                self.end_headers()
                self.wfile.write(json_bytes)
                return

        self.send_error(404, "Endpoint Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/scan":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                params = json.loads(post_data.decode("utf-8")) if post_data else {}
            except Exception:
                params = {}

            if scanner_instance.is_scanning:
                self._send_json({"error": "Scan already in progress"}, status=409)
                return

            mode = params.get("mode", "real")
            subnet = params.get("subnet", None)

            # Run scan in background daemon thread
            if mode == "demo":
                t = threading.Thread(target=scanner_instance.run_demo_scan, daemon=True)
            else:
                t = threading.Thread(target=scanner_instance.run_real_scan, args=(subnet,), daemon=True)
            t.start()

            self._send_json({"message": "Scan started successfully", "mode": mode})
            return

        self.send_error(404, "Endpoint Not Found")


def run_server(host="0.0.0.0", port=5000, open_browser=True, auto_demo=False):
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, NetworkScannerHandler)
    url = f"http://localhost:{port}"

    print("=" * 65)
    print("  🌐 NetPulse: Advanced Local Network Scanner & Web Dashboard")
    print("=" * 65)
    print(f"  • Server running on: {url}")
    print(f"  • Local Gateway detected: {scanner_instance.gateway_ip}")
    print(f"  • Subnet: {scanner_instance.subnet}")
    print("  • Press Ctrl+C to stop the server anytime.")
    print("=" * 65)

    if auto_demo:
        print("  [i] Auto-triggering initial demo scan for preview...")
        t = threading.Thread(target=scanner_instance.run_demo_scan, daemon=True)
        t.start()

    if open_browser:
        def _open():
            import time
            time.sleep(1.0)
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down NetPulse server. Goodbye!")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NetPulse: University Network Scanner Web App")
    parser.add_argument("--port", type=int, default=5000, help="Web server port (default: 5000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind to (default: 0.0.0.0)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open default web browser")
    parser.add_argument("--demo", action="store_true", help="Auto-populate with simulated network devices on launch")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port, open_browser=not args.no_browser, auto_demo=args.demo)
