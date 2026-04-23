from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import webview
from webview.dom import DOMEventHandler

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
    """Vueアプリケーションを表示するためのエントリURLを解決する。"""

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


def create_drop_items(event: dict[str, Any]) -> list[dict[str, str]]:
    """pywebviewのドロップイベントから登録処理用のファイル情報を生成する。"""

    data_transfer = event.get("dataTransfer")
    if not isinstance(data_transfer, dict):
        return []

    files = data_transfer.get("files")
    if not isinstance(files, list):
        return []

    items: list[dict[str, str]] = []
    for file in files:
        if not isinstance(file, dict):
            continue

        raw_path = str(file.get("pywebviewFullPath") or "").strip()
        if not raw_path:
            continue

        path = Path(raw_path).expanduser().resolve()
        items.append(
            {
                "path": str(path),
                "type": "directory" if path.is_dir() else "file",
            }
        )

    return items


def register_handlers(window: object, api: AppApi) -> None:
    """pywebviewのDOMイベントにドラッグ＆ドロップ処理を登録する。"""

    def on_drag(event: dict[str, Any]) -> None:
        """ドラッグ中のイベントを受け取り、発生したイベント種別をログ出力する。"""

        print(f"Event: {event.get('type', 'drag')}")

    def on_drop(event: dict[str, Any]) -> None:
        """ドロップされたファイルまたはフォルダを既存の登録処理へ渡す。"""

        items = create_drop_items(event)
        if not items:
            print("Event: drop. Dropped files were not available.")
            return

        for item in items:
            print(item["path"])

        result = api.import_selected_items({"items": items})
        if result.get("success"):
            data = result.get("data") or {}
            print(
                "Drop import completed. "
                f"Imported: {data.get('importedCount', 0)}, "
                f"Skipped: {data.get('skippedCount', 0)}"
            )
            window.evaluate_js(
                "window.dispatchEvent(new CustomEvent("
                "'azviewer:import-complete', "
                f"{{ detail: {json.dumps(data)} }}"
                "));"
            )
            return

        print(f"Drop import failed: {result.get('message', '')}", file=sys.stderr)

    window.dom.document.events.dragenter += DOMEventHandler(on_drag, True, True)
    window.dom.document.events.dragstart += DOMEventHandler(on_drag, True, True)
    window.dom.document.events.dragover += DOMEventHandler(on_drag, True, True, debounce=500)
    window.dom.document.events.drop += DOMEventHandler(on_drop, True, True)
    window.dom.document.events.load += DOMEventHandler(lambda _: api.bootstrap_app(), True, True)


def main() -> int:
    """アプリケーションの起動処理を実行し、終了コードを返す。"""

    try:
        entry_url = resolve_entry_url()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    api = AppApi()

    window = webview.create_window(
        APP_TITLE,
        entry_url,
        js_api=api,
        width=1200,
        height=800,
        min_size=(900, 600),
    )
    try:
        webview.start(register_handlers, [window, api]) # debug option. debug=True
    finally:
        api.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
