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
            webview.FileDialog.OPEN,
            allow_multiple=True,
            file_types=self.IMAGE_FILE_TYPES,
        )
        return [{"path": str(Path(path).resolve()), "type": "file"} for path in selected or []]

    def select_folder(self) -> list[dict[str, str]]:
        """フォルダ選択ダイアログを開き、選択されたフォルダ情報を返す。"""

        window = self._get_window()
        selected = window.create_file_dialog(webview.FileDialog.FOLDER)
        return [
            {"path": str(Path(path).resolve()), "type": "directory"}
            for path in selected or []
        ]

    def select_text_file_for_append(self) -> str | None:
        """追記先の既存テキストファイルを選択する。"""

        window = self._get_window()
        selected = window.create_file_dialog(
            webview.FileDialog.OPEN,
            allow_multiple=False,
            file_types=("Text files (*.txt)", "All files (*.*)"),
        )
        return self._first_dialog_path(selected)

    def select_text_file_for_save(self) -> str | None:
        """新規保存先のテキストファイルを選択する。"""

        window = self._get_window()
        selected = window.create_file_dialog(
            webview.FileDialog.SAVE,
            save_filename="wildcard.txt",
            file_types=("Text files (*.txt)", "All files (*.*)"),
        )
        selected_path = self._first_dialog_path(selected)
        if not selected_path:
            return None

        path = Path(selected_path)
        if path.suffix.lower() != ".txt":
            path = path.with_suffix(".txt")
        return str(path)

    def _first_dialog_path(self, selected: object) -> str | None:
        """pywebviewのダイアログ返却値から先頭パスを取り出す。"""

        if not selected:
            return None
        if isinstance(selected, (list, tuple)):
            return str(selected[0]) if selected else None
        return str(selected)

    def _get_window(self):
        """ダイアログ表示に利用するpywebviewウィンドウを取得する。"""

        window = self._window_provider()
        if window is None:
            raise RuntimeError("Application window is not available.")
        return window
