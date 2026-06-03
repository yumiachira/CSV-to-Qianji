import json
import os
import socket
import sys
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from py.db_manager import (
    add_entry,
    delete_entry,
    edit_entry,
    search_entries,
    sync_db,
)

def get_project_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent

PROJECT_ROOT = get_project_root()
PORT = 8000
pending_names = []


def set_pending_names(names):
    global pending_names
    pending_names = []
    seen = set()
    for name in names:
        name = (name or "").strip()
        if name and name not in seen:
            seen.add(name)
            pending_names.append(name)


class UpdateDBRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Always serve files from project root, not current working directory
        path = urlparse(path).path
        if path == "/":
            path = "/updateDB.html"
        return str(PROJECT_ROOT / path.lstrip("/"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/records":
            query = parse_qs(parsed.query).get("q", [""])[0]
            self._send_json(search_entries(query))
            return
        if path == "/api/pending":
            self._send_json(pending_names)
            return
        if path == "/api/reload":
            sync_db()
            self._send_json({"status": "ok"})
            return
        if path == "/api/health":
            self._send_json({"status": "ok"})
            return
        return super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(body or "{}")
        except json.JSONDecodeError:
            payload = {}

        if self.path == "/api/add":
            name = payload.get("name", "")
            type1 = payload.get("type1", "")
            type2 = payload.get("type2", "")
            add_entry(name, type1, type2)
            sync_db()
            self._send_json({"status": "ok"})
            return
        if self.path == "/api/edit":
            name = payload.get("name", "")
            type1 = payload.get("type1", "")
            type2 = payload.get("type2", "")
            ok = edit_entry(name, type1, type2)
            if not ok:
                self._send_json({"status": "error", "message": "未找到要编辑的 Name"}, status=404)
                return
            sync_db()
            self._send_json({"status": "ok"})
            return
        if self.path == "/api/delete":
            name = payload.get("name", "")
            ok = delete_entry(name)
            if not ok:
                self._send_json({"status": "error", "message": "未找到要删除的 Name"}, status=404)
                return
            sync_db()
            self._send_json({"status": "ok"})
            return
        self.send_error(404, "Not Found")

    def _send_json(self, data, status=200):
        text = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(text)))
        self.end_headers()
        self.wfile.write(text)


def find_free_port(start_port=8000, max_port=9000):
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("无法找到可用端口")


def run_server(open_browser=True):
    os.chdir(PROJECT_ROOT)
    port = find_free_port(PORT)
    address = ("127.0.0.1", port)
    server = HTTPServer(address, UpdateDBRequestHandler)
    url = f"http://127.0.0.1:{port}/updateDB.html"
    print(f"🔧 UpdateDB UI 启动：{url}")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 UpdateDB 服务器已停止")
    finally:
        server.server_close()


if __name__ == "__main__":
    set_pending_names([])
    run_server(open_browser=True)
