from __future__ import annotations

import os
import sys
from pathlib import Path

import webview

APP_TITLE = "AZViewer"
ROOT_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from .api.app_api import AppApi
except ImportError:
    from backend.api.app_api import AppApi


FRONTEND_DIST = ROOT_DIR / "frontend" / "dist" / "index.html"


def resolve_entry_url() -> str:
    dev_server_url = os.environ.get("AZVIEWER_FRONTEND_URL")
    if dev_server_url:
        return dev_server_url

    if FRONTEND_DIST.exists():
        return FRONTEND_DIST.as_uri()

    raise FileNotFoundError(
        "frontend/dist/index.html was not found. "
        "Run `npm install` and `npm run build` in the frontend directory first, "
        "or set AZVIEWER_FRONTEND_URL to a running Vite dev server."
    )


def main() -> int:
    try:
        entry_url = resolve_entry_url()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    api = AppApi()
    try:
        api.initialize_app_backend()
    except Exception as exc:
        print(f"Application initialization failed: {exc}", file=sys.stderr)
        api.close()
        return 1

    webview.create_window(
        APP_TITLE,
        entry_url,
        js_api=api,
        width=1200,
        height=800,
        min_size=(900, 600),
    )
    try:
        webview.start() # debug option. debug=True
    finally:
        api.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
