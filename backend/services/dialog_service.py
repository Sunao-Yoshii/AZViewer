from __future__ import annotations

from pathlib import Path
from typing import Callable

import webview


class DialogService:
    """pywebviewのネイティブダイアログを使ったファイル選択処理を提供する。"""

    IMAGE_FILE_TYPES = (
        "Image Files (*.png;*.jpg;*.jpeg;*.webp;*.avif)",
        "All files (*.*)",
    )

    def __init__(self, window_provider: Callable[[], object | None]) -> None:
        """ダイアログ表示に利用するウィンドウ取得関数を保持する。"""

        self._window_provider = window_provider

    def select_files(self) -> list[dict[str, str]]:
        """画像ファイル選択ダイアログを開き、選択されたファイル情報を返す。"""

        window = self._get_window()
        selected = window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=self.IMAGE_FILE_TYPES,
        )
        return [{"path": str(Path(path).resolve()), "type": "file"} for path in selected or []]

    def select_folder(self) -> list[dict[str, str]]:
        """フォルダ選択ダイアログを開き、選択されたフォルダ情報を返す。"""

        window = self._get_window()
        selected = window.create_file_dialog(webview.FOLDER_DIALOG)
        return [
            {"path": str(Path(path).resolve()), "type": "directory"}
            for path in selected or []
        ]

    def _get_window(self):
        """ダイアログ表示に利用するpywebviewウィンドウを取得する。"""

        window = self._window_provider()
        if window is None:
            raise RuntimeError("Application window is not available.")
        return window
