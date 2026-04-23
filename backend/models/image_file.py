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
class ImageFileListItem:
    """画像一覧表示用の1件分データを表す。"""

    id: int
    filename: str
    path: str
    folder: str
    rating: str
    is_checked: int
    is_favorite: int
    comment: str | None = None

    def to_dict(self) -> dict[str, object]:
        """API返却用の辞書形式へ変換する。"""

        return {
            "id": self.id,
            "filename": self.filename,
            "path": self.path,
            "folder": self.folder,
            "rating": self.rating,
            "is_checked": self.is_checked,
            "is_favorite": self.is_favorite,
            "comment": self.comment,
        }


@dataclass(frozen=True)
class SearchImageFilesResult:
    """画像一覧検索結果を表す。"""

    items: list[ImageFileListItem]
    total_count: int
    total_pages: int
    page: int
    page_size: int

    def to_dict(self) -> dict[str, object]:
        """API返却用の辞書形式へ変換する。"""

        return {
            "items": [item.to_dict() for item in self.items],
            "total_count": self.total_count,
            "total_pages": self.total_pages,
            "page": self.page,
            "page_size": self.page_size,
        }


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
