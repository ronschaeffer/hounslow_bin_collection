"""
Lightweight HTTP server for serving ICS calendar files.

Uses Python's built-in http.server — no extra dependencies required.
"""

from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CalendarRequestHandler(SimpleHTTPRequestHandler):
    """Serves files from the output directory with correct MIME types."""

    def log_message(self, format, *args):
        logger.info(format, *args)

    def end_headers(self):
        # Allow CORS for calendar apps
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()


def start_server(output_dir: str, host: str = "0.0.0.0", port: int = 8080) -> None:
    """Start the HTTP server to serve calendar files.

    Args:
        output_dir: Directory containing the ICS files
        host: Bind address
        port: Port to listen on
    """
    path = Path(output_dir)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    handler = partial(CalendarRequestHandler, directory=str(path))
    server = HTTPServer((host, port), handler)
    logger.info("Serving calendar files from %s on %s:%s", output_dir, host, port)
    server.serve_forever()
