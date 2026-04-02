"""
Lightweight HTTP server for the bin collection dashboard and ICS calendar files.

Uses Python's built-in http.server — no extra dependencies required.
Serves:
  /              — HTML dashboard
  /dashboard     — HTML dashboard (alias)
  /data.json     — bin collection JSON data
  /*.ics         — ICS calendar files
"""

from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Resolved once at module level by start_server()
_dashboard_html: str | None = None


class BinCollectionRequestHandler(SimpleHTTPRequestHandler):
    """Serves dashboard, JSON data, and ICS files from the output directory."""

    def log_message(self, format, *args):
        logger.info(format, *args)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_GET(self):
        # Dashboard routes
        if self.path in ("/", "/dashboard"):
            self._serve_dashboard()
            return

        # JSON data alias — serves bin_collections.json from output dir
        if self.path == "/data.json":
            self.path = "/bin_collections.json"

        # Fall through to default static file serving (ICS, JSON, etc.)
        super().do_GET()

    def _serve_dashboard(self):
        if _dashboard_html is None:
            self.send_error(404, "Dashboard not found")
            return
        body = _dashboard_html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_server(output_dir: str, host: str = "0.0.0.0", port: int = 8080) -> None:
    """Start the HTTP server.

    Args:
        output_dir: Directory containing the ICS and JSON files
        host: Bind address
        port: Port to listen on
    """
    global _dashboard_html

    path = Path(output_dir)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    # Load dashboard HTML — look in common locations
    dashboard_path = None
    candidates = [
        Path(__file__).resolve().parents[3] / "assets" / "dashboard.html",
        Path("/app/assets/dashboard.html"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            dashboard_path = candidate
            break

    if dashboard_path:
        _dashboard_html = dashboard_path.read_text(encoding="utf-8")
        logger.info("Dashboard loaded from %s", dashboard_path)
    else:
        logger.warning("Dashboard HTML not found, serving files only")

    handler = partial(BinCollectionRequestHandler, directory=str(path))
    server = HTTPServer((host, port), handler)
    logger.info("Serving on %s:%s (output=%s)", host, port, output_dir)
    server.serve_forever()
