from __future__ import annotations

import json
import os
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, TextIO

import webview
from webview.dom import DOMEventHandler

APP_TITLE = "AZViewer"
ROOT_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else ROOT_DIR

try:
    from .api.app_api import AppApi
except ImportError:
    from backend.api.app_api import AppApi


FRONTEND_DIST = ROOT_DIR / "frontend" / "dist" / "index.html"
SMOKE_TEST_ARGUMENT = "--smoke-test-runtime"
LOG_FILE_NAME = "azviewer.log"


class TeeStream:
    """Write process output to both the original stream and the log file."""

    def __init__(self, original: TextIO | None, log_file: TextIO) -> None:
        self._original = original
        self._log_file = log_file

    def write(self, message: str) -> int:
        if self._original:
            self._original.write(message)

        return self._log_file.write(message)

    def flush(self) -> None:
        if self._original:
            self._original.flush()

        self._log_file.flush()


def candidate_log_dirs() -> list[Path]:
    """Return writable log directory candidates in preference order."""

    configured_log_dir = os.environ.get("AZVIEWER_LOG_DIR")
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    candidates = [
        local_app_data / "AZViewer" / "logs",
        APP_DIR / "logs",
        Path.cwd() / "logs",
        Path(tempfile.gettempdir()) / "AZViewer" / "logs",
    ]
    if configured_log_dir:
        candidates.insert(0, Path(configured_log_dir))

    return candidates


def open_startup_log() -> tuple[TextIO, Path]:
    """Open the first writable startup log file."""

    last_error: OSError | None = None
    for log_dir in candidate_log_dirs():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / LOG_FILE_NAME
            return log_path.open("a", encoding="utf-8"), log_path
        except OSError as exc:
            last_error = exc

    raise RuntimeError("Could not open AZViewer startup log.") from last_error


def configure_startup_logging() -> tuple[TextIO, TextIO | None, TextIO | None]:
    """Persist startup diagnostics for windowed executions without a console."""

    log_file, log_path = open_startup_log()
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    log_file.write(f"\n=== AZViewer startup: {log_path} ===\n")
    log_file.flush()
    sys.stdout = TeeStream(original_stdout, log_file)  # type: ignore[assignment]
    sys.stderr = TeeStream(original_stderr, log_file)  # type: ignore[assignment]
    return log_file, original_stdout, original_stderr


def run_with_startup_logging() -> int:
    """Run the app and record failures that would otherwise be invisible."""

    log_file, original_stdout, original_stderr = configure_startup_logging()
    try:
        return main()
    except Exception:
        print("Unhandled startup error:", file=sys.stderr)
        traceback.print_exc()
        return 1
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        sys.stdout = original_stdout  # type: ignore[assignment]
        sys.stderr = original_stderr  # type: ignore[assignment]
        log_file.close()


def smoke_test_runtime() -> int:
    """Packaged runtime dependencies needed by pywebview on Windows are importable."""

    try:
        import clr  # noqa: F401
        import webview.platforms.winforms  # noqa: F401
    except Exception as exc:
        print(f"Runtime smoke test failed: {exc}", file=sys.stderr)
        return 1

    print("Runtime smoke test passed.")
    return 0


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


def dispatch_frontend_event(window: object, event_name: str, detail: dict[str, Any]) -> None:
    """Vue側へCustomEventを発生させる。"""

    window.evaluate_js(
        "window.dispatchEvent(new CustomEvent("
        f"{json.dumps(event_name)}, "
        f"{{ detail: {json.dumps(detail)} }}"
        "));"
    )


def create_import_event_detail(result: dict[str, Any]) -> dict[str, Any]:
    """インポートAPI結果をフロントエンドイベント用detailへ変換する。"""

    return {
        "success": bool(result.get("success")),
        "message": str(result.get("message") or ""),
        "data": result.get("data") or {},
    }


def register_handlers(window: object, api: AppApi) -> None:
    """pywebviewのDOMイベントにドラッグ＆ドロップ処理を登録する。"""

    def on_drop(event: dict[str, Any]) -> None:
        """ドロップされたファイルまたはフォルダを既存の登録処理へ渡す。"""

        print("Event: drop")
        items = create_drop_items(event)
        if not items:
            print("Event: drop. Dropped files were not available.")
            dispatch_frontend_event(
                window,
                "azviewer:import-complete",
                {
                    "success": False,
                    "message": "Dropped files were not available.",
                    "data": {},
                },
            )
            return

        for item in items:
            print(item["path"])

        dispatch_frontend_event(
            window,
            "azviewer:import-start",
            {
                "fileCount": len(items),
            },
        )
        result = api.import_selected_items({"items": items})
        detail = create_import_event_detail(result)
        if result.get("success"):
            data = detail["data"]
            print(
                "Drop import completed. "
                f"Imported: {data.get('importedCount', 0)}, "
                f"Skipped: {data.get('skippedCount', 0)}"
            )
            dispatch_frontend_event(window, "azviewer:import-complete", detail)
            return

        print(f"Drop import failed: {result.get('message', '')}", file=sys.stderr)
        dispatch_frontend_event(window, "azviewer:import-complete", detail)

    window.dom.document.events.drop += DOMEventHandler(on_drop, True, True)


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
    if SMOKE_TEST_ARGUMENT in sys.argv:
        raise SystemExit(smoke_test_runtime())

    raise SystemExit(run_with_startup_logging())
