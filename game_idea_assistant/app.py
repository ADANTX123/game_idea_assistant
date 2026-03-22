from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from assistant import GameIdeaAssistant


ROOT_DIR = Path(__file__).resolve().parent
STATIC_DIR = ROOT_DIR / "static"
ASSISTANT = GameIdeaAssistant(ROOT_DIR)


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json(ASSISTANT.health())
            return
        if parsed.path == "/api/logs":
            self._send_json({"items": ASSISTANT.recent_runs()})
            return
        if parsed.path == "/api/settings":
            self._send_json({"settings": ASSISTANT.get_settings_summary()})
            return

        self._serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/generate":
            self._handle_generate()
            return
        if parsed.path == "/api/settings":
            self._handle_settings_update()
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def _handle_generate(self) -> None:
        payload = self._read_json_body()
        if payload is None:
            return

        idea = str(payload.get("idea", "")).strip()
        if not idea:
            self._send_json({"error": "idea is required"}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            result = ASSISTANT.run(idea)
        except ValueError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            return

        self._send_json(result)

    def _handle_settings_update(self) -> None:
        payload = self._read_json_body()
        if payload is None:
            return

        settings = ASSISTANT.update_settings(payload)
        self._send_json({"settings": settings})

    def _read_json_body(self) -> dict[str, object] | None:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        try:
            return json.loads(raw_body or "{}")
        except json.JSONDecodeError:
            self._send_json({"error": "invalid json body"}, status=HTTPStatus.BAD_REQUEST)
            return None

    def _serve_static(self, request_path: str) -> None:
        relative_path = "index.html" if request_path in ("/", "") else request_path.lstrip("/")
        file_path = STATIC_DIR / relative_path
        if not file_path.exists() or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        mime_type, _ = mimetypes.guess_type(str(file_path))
        content = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string: str, *args: object) -> None:
        return


def main() -> None:
    host = "127.0.0.1"
    port = 8010
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Game Idea Assistant running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
