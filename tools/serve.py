"""Local preview server that applies Netlify-style _headers (CSP etc.) so CSP problems show up locally.

Usage (repo root): python tools/serve.py [port]
"""
import fnmatch
import http.server
import sys
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse_headers():
    rules, current = [], None
    for raw in (ROOT / "_headers").read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw.startswith((" ", "\t")):
            current = (raw.strip(), [])
            rules.append(current)
        elif current and ":" in raw:
            k, v = raw.strip().split(":", 1)
            current[1].append((k.strip(), v.strip()))
    return rules


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".glb": "model/gltf-binary", ".webmanifest": "application/manifest+json",
                      ".avif": "image/avif", ".webp": "image/webp", ".woff2": "font/woff2",
                      ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json",
                      ".webm": "video/webm", ".svg": "image/svg+xml"}

    def end_headers(self):
        path = self.path.split("?", 1)[0]
        for pattern, headers in parse_headers():
            if fnmatch.fnmatch(path, pattern):
                for k, v in headers:
                    if k.lower() != "content-type":
                        self.send_header(k, v)
        super().end_headers()

    def send_error(self, code, message=None, explain=None):
        if code == 404 and (ROOT / "404.html").exists():
            body = (ROOT / "404.html").read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().send_error(code, message, explain)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    http.server.ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(ROOT))).serve_forever()
