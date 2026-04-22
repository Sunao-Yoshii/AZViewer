from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImageFileRecord:
    """データベースへ保存する画像ファイル1件分の情報を表す。"""

    filename: str
    path: str
    folder: str
    rating: str = "General"
    is_checked: int = 0
    is_favorite: int = 0
    comment: str | None = None


@dataclass(frozen=True)
class ImportResult:
    """画像ファイル登録処理の結果を表す。"""

    success: bool
    error_summary: str | None = None
    failed_files: list[str] | None = None
    message: str = ""
    imported_count: int = 0
    skipped_count: int = 0

    def to_api_data(self) -> dict[str, object] | None:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        if self.success:
            return {
                "importedCount": self.imported_count,
                "skippedCount": self.skipped_count,
            }

        return {
            "errorSummary": self.error_summary or "データ登録中にエラーが発生しました。",
            "failedFiles": self.failed_files or [],
        }
