"""Vercel Python entry — routes /api/* to GARAKLAND server.Handler."""
from __future__ import annotations

import os
import sys
from io import BytesIO
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import Handler, setup  # noqa: E402

_INITIALIZED = False


class _HeaderMap:
    def __init__(self, items):
        self._m = {k.lower(): v for k, v in items}

    def get(self, name, default=None):
        return self._m.get(name.lower(), default)


def _parse_http(raw: bytes):
    if not raw:
        return 500, {"Content-Type": "application/json"}, b'{"error":"empty response"}'
    head, _, body = raw.partition(b"\r\n\r\n")
    lines = head.decode("iso-8859-1", errors="replace").split("\r\n")
    status = 500
    if lines:
        parts = lines[0].split(" ", 2)
        if len(parts) >= 2 and parts[1].isdigit():
            status = int(parts[1])
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip()] = v.strip()
    return status, headers, body


def _invoke(method: str, path: str, headers: dict, body: bytes) -> tuple[int, dict, bytes]:
    out = BytesIO()

    class OneShot(Handler):
        def __init__(self):
            self.rfile = BytesIO(body)
            self.wfile = out
            self.raw_requestline = f"{method} {path} HTTP/1.1".encode()
            self.requestline = self.raw_requestline.decode()
            self.command = method
            self.request_version = "HTTP/1.1"
            self.path = path
            self.headers = _HeaderMap(headers.items())
            self.client_address = ("127.0.0.1", 0)
            self.server = object()

    h = OneShot()
    if method == "GET":
        h.do_GET()
    elif method == "POST":
        h.do_POST()
    elif method == "OPTIONS":
        h.send_response(204)
        h.send_header("Access-Control-Allow-Origin", os.environ.get("GARAK_PUBLIC_BASE_URL", "*"))
        h.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        h.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, X-Garak-Client, X-Garak-Admin-Token, X-Garak-Merchant-Key",
        )
        h.end_headers()
    else:
        h.send_error(405)
    return _parse_http(out.getvalue())


def handler(request):
    global _INITIALIZED
    if not _INITIALIZED:
        setup()
        _INITIALIZED = True

    method = getattr(request, "method", "GET") or "GET"
    path = getattr(request, "path", "/") or "/"
    query = getattr(request, "query", None) or {}
    if query and "?" not in path:
        path = path + "?" + urlencode(query, doseq=True)

    body_raw = getattr(request, "body", b"") or b""
    if isinstance(body_raw, str):
        body_raw = body_raw.encode("utf-8")

    hdrs = {}
    req_headers = getattr(request, "headers", {}) or {}
    for k, v in req_headers.items():
        hdrs[k] = v

    status, headers, body = _invoke(method, path, hdrs, body_raw)
    return {"statusCode": status, "headers": headers, "body": body.decode("utf-8", errors="replace")}


app = handler
application = handler
