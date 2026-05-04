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
    tags: list[str] | None = None

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
            "tags": self.tags or [],
        }


@dataclass(frozen=True)
class TagListItem:
    """タグ検索候補の1件分データを表す。"""

    id: int
    name: str

    def to_dict(self) -> dict[str, object]:
        """API返却用の辞書形式へ変換する。"""

        return {
            "id": self.id,
            "name": self.name,
        }


@dataclass(frozen=True)
class FolderListItem:
    """フォルダ検索候補の1件分データを表す。"""

    name: str
    image_count: int

    def to_dict(self) -> dict[str, object]:
        """API返却用の辞書形式へ変換する。"""

        return {
            "name": self.name,
            "image_count": self.image_count,
        }


@dataclass(frozen=True)
class DuplicateTagSetItem:
    """重複しているタグ構成の1件分データを表す。"""

    hash: str
    tag_set: str
    tag_names: str
    image_count: int

    def to_dict(self) -> dict[str, object]:
        """API返却用の辞書形式へ変換する。"""

        return {
            "hash": self.hash,
            "tagSet": self.tag_set,
            "tagNames": self.tag_names,
            "imageCount": self.image_count,
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
class PromptTagImportFailure:
    """プロンプト一括タグ登録で失敗した画像1件分を表す。"""

    id: int
    path: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        """API返却用の辞書形式へ変換する。"""

        return {
            "id": self.id,
            "path": self.path,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class PromptTagImportResult:
    """プロンプト一括タグ登録処理の結果を表す。"""

    target_count: int
    processed_count: int
    tagged_count: int
    skipped_count: int
    failed_count: int
    failed_files: list[PromptTagImportFailure]

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "targetCount": self.target_count,
            "processedCount": self.processed_count,
            "taggedCount": self.tagged_count,
            "skippedCount": self.skipped_count,
            "failedCount": self.failed_count,
            "failedFiles": [
                item.to_dict()
                for item in self.failed_files[:20]
            ],
        }


@dataclass(frozen=True)
class PhysicalDeleteFailure:
    """物理削除で失敗した画像1件分を表す。"""

    id: int
    path: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        """API返却用の辞書形式へ変換する。"""

        return {
            "id": self.id,
            "path": self.path,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class PhysicalDeleteResult:
    """画像ファイルの一括物理削除処理結果を表す。"""

    target_count: int
    deleted_file_count: int
    deleted_thumbnail_count: int
    deleted_record_count: int
    missing_file_count: int
    failed_count: int
    failed_files: list[PhysicalDeleteFailure]

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "targetCount": self.target_count,
            "deletedFileCount": self.deleted_file_count,
            "deletedThumbnailCount": self.deleted_thumbnail_count,
            "deletedRecordCount": self.deleted_record_count,
            "missingFileCount": self.missing_file_count,
            "failedCount": self.failed_count,
            "failedFiles": [
                item.to_dict()
                for item in self.failed_files[:20]
            ],
        }


@dataclass(frozen=True)
class FileMoveFailure:
    """ファイル移動で失敗した画像1件分を表す。"""

    id: int
    path: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        """API返却用の辞書形式へ変換する。"""

        return {
            "id": self.id,
            "path": self.path,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class FileMoveResult:
    """画像ファイルの一括移動処理結果を表す。"""

    target_count: int
    moved_count: int
    skipped_count: int
    failed_count: int
    failed_files: list[FileMoveFailure]

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "targetCount": self.target_count,
            "movedCount": self.moved_count,
            "skippedCount": self.skipped_count,
            "failedCount": self.failed_count,
            "failedFiles": [
                item.to_dict()
                for item in self.failed_files[:20]
            ],
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
