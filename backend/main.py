from __future__ import annotations

import os
import sys
from pathlib import Path

import webview

try:
    from .api.app_api import AppApi
except ImportError:
    from api.app_api import AppApi


APP_TITLE = "AZViewer"
ROOT_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
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

    webview.create_window(
        APP_TITLE,
        entry_url,
        js_api=AppApi(),
        width=1200,
        height=800,
        min_size=(900, 600),
    )
    webview.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
