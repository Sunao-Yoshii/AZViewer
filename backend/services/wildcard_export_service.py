from __future__ import annotations

from pathlib import Path

from backend.models import WildcardExportResult
from backend.services.dialog_service import DialogService


class WildcardExportService:
    """Stable Diffusion WebUI向けワイルドカードテキストを保存する。"""

    def __init__(self, dialog_service: DialogService) -> None:
        """保存先選択に利用するダイアログサービスを保持する。"""

        self._dialog_service = dialog_service

    def export_text(self, mode: str, text: str) -> WildcardExportResult:
        """出力方式に応じてワイルドカードテキストを保存または追記する。"""

        normalized_mode = self._normalize_mode(mode)
        normalized_text = self._normalize_output_text(text)
        if not normalized_text:
            raise ValueError("出力対象のテキストがありません。")

        selected_path = self._select_output_path(normalized_mode)
        if not selected_path:
            return WildcardExportResult(
                path="",
                mode=normalized_mode,
                line_count=0,
                cancelled=True,
            )

        output_path = Path(selected_path)
        if normalized_mode == "create":
            self._write_text(output_path, normalized_text)
        else:
            self._append_text(output_path, normalized_text)

        return WildcardExportResult(
            path=str(output_path),
            mode=normalized_mode,
            line_count=self._count_lines(normalized_text),
            cancelled=False,
        )

    def _normalize_mode(self, mode: str) -> str:
        """出力方式を検証して正規化する。"""

        value = str(mode or "").strip()
        if value not in ("create", "append"):
            raise ValueError("出力方式が不正です。")
        return value

    def _normalize_output_text(self, value: str) -> str:
        """空行を除外し、改行コードをCRLFへ正規化する。"""

        lines = [
            line.strip()
            for line in str(value or "").splitlines()
            if line.strip()
        ]
        return "\r\n".join(lines)

    def _select_output_path(self, mode: str) -> str | None:
        """出力方式に応じて保存先または追記先を選択する。"""

        if mode == "create":
            return self._dialog_service.select_text_file_for_save()
        return self._dialog_service.select_text_file_for_append()

    def _count_lines(self, text: str) -> int:
        """空行を除いた出力行数を返す。"""

        return len([line for line in text.splitlines() if line.strip()])

    def _write_text(self, path: Path, text: str) -> None:
        """UTF-8 BOMなし、CRLF終端で新規保存する。"""

        with path.open("w", encoding="utf-8", newline="") as file:
            file.write(text)
            file.write("\r\n")

    def _append_text(self, path: Path, text: str) -> None:
        """既存末尾の改行を補正してUTF-8 BOMなしで追記する。"""

        needs_newline = self._needs_leading_newline(path)
        with path.open("a", encoding="utf-8", newline="") as file:
            if needs_newline:
                file.write("\r\n")
            file.write(text)
            file.write("\r\n")

    def _needs_leading_newline(self, path: Path) -> bool:
        """追記前に既存ファイル末尾へ改行が必要か判定する。"""

        if not path.exists() or path.stat().st_size == 0:
            return False

        with path.open("rb") as file:
            file.seek(-1, 2)
            return file.read(1) not in (b"\n", b"\r")
