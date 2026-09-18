"""Serve the local Apple Music authorization helper without exposing the repo."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "music-auth"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        routes = {"/": ("index.html", "text/html; charset=utf-8"),
                  "/token.mjs": ("token.mjs", "text/javascript; charset=utf-8")}
        route = routes.get(self.path)
        if not route:
            self.send_error(404)
            return
        name, content_type = route
        body = (ROOT / name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8765), Handler)
    print("Apple Music setup: http://127.0.0.1:8765", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
