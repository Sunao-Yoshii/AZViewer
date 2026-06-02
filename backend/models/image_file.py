from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImageFileRecord:
    """データベースへ保存する画像ファイル1件分の情報を表す。"""

    filename: str
    path: str
    folder_path: str
    folder_name: str
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
    folder_id: int
    folder_path: str
    rating: str
    is_checked: int
    is_favorite: int
    comment: str | None = None
    tags: list[str] | None = None
    model_name: str | None = None

    def to_dict(self) -> dict[str, object]:
        """API返却用の辞書形式へ変換する。"""

        return {
            "id": self.id,
            "filename": self.filename,
            "path": self.path,
            "folder": self.folder,
            "folderId": self.folder_id,
            "folderPath": self.folder_path,
            "rating": self.rating,
            "is_checked": self.is_checked,
            "is_favorite": self.is_favorite,
            "comment": self.comment,
            "tags": self.tags or [],
            "modelName": self.model_name,
        }


@dataclass(frozen=True)
class BulkAttributeUpdateResult:
    """画像属性の一括更新処理結果を表す。"""

    target_count: int
    updated_count: int

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "targetCount": self.target_count,
            "updatedCount": self.updated_count,
        }


@dataclass(frozen=True)
class TagCaptionExportFailure:
    """タグcaption出力で失敗した画像1件分を表す。"""

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
class TagCaptionExportResult:
    """選択画像タグcaption出力処理の結果を表す。"""

    target_count: int
    exported_count: int
    skipped_count: int
    failed_count: int
    failed_files: list[TagCaptionExportFailure]

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "targetCount": self.target_count,
            "exportedCount": self.exported_count,
            "skippedCount": self.skipped_count,
            "failedCount": self.failed_count,
            "failedFiles": [
                item.to_dict()
                for item in self.failed_files[:20]
            ],
        }


@dataclass(frozen=True)
class CaptionTagImportFailure:
    """captionタグ読み込みで失敗した画像1件分を表す。"""

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
class CaptionTagImportResult:
    """captionタグ読み込み処理の結果を表す。"""

    target_count: int
    updated_count: int
    skipped_count: int
    failed_count: int
    failed_files: list[CaptionTagImportFailure]

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "targetCount": self.target_count,
            "updatedCount": self.updated_count,
            "skippedCount": self.skipped_count,
            "failedCount": self.failed_count,
            "failedFiles": [
                item.to_dict()
                for item in self.failed_files[:20]
            ],
        }


@dataclass(frozen=True)
class BulkTagAddFailure:
    """一括タグ追加で失敗した画像1件分を表す。"""

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
class BulkTagAddResult:
    """一括タグ追加処理の結果を表す。"""

    target_count: int
    updated_count: int
    skipped_count: int
    failed_count: int
    failed_files: list[BulkTagAddFailure]

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "targetCount": self.target_count,
            "updatedCount": self.updated_count,
            "skippedCount": self.skipped_count,
            "failedCount": self.failed_count,
            "failedFiles": [
                item.to_dict()
                for item in self.failed_files[:20]
            ],
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

    id: int
    name: str
    path: str
    image_count: int

    def to_dict(self) -> dict[str, object]:
        """API返却用の辞書形式へ変換する。"""

        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "imageCount": self.image_count,
        }


@dataclass(frozen=True)
class ImageFolderMaintenanceItem:
    """フォルダメンテナンス候補の1件分データを表す。"""

    id: int
    name: str
    path: str
    image_count: int

    def to_dict(self) -> dict[str, object]:
        """API返却用の辞書形式へ変換する。"""

        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "imageCount": self.image_count,
        }


@dataclass(frozen=True)
class ImageFolderReference:
    """フォルダ単位操作で参照するフォルダ定義を表す。"""

    id: int
    name: str
    path: str


@dataclass(frozen=True)
class UnusedFolderDeleteResult:
    """未使用フォルダマスタ削除処理の結果を表す。"""

    deleted_count: int

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "deletedCount": self.deleted_count,
        }


@dataclass(frozen=True)
class ImageModelListItem:
    """モデル検索候補の1件分データを表す。"""

    name: str
    image_count: int

    def to_dict(self) -> dict[str, object]:
        """API返却用の辞書形式へ変換する。"""

        return {
            "name": self.name,
            "image_count": self.image_count,
        }


@dataclass(frozen=True)
class MasterMaintenanceItem:
    """マスタメンテナンス候補の1件分データを表す。"""

    id: int
    name: str
    image_count: int

    def to_dict(self) -> dict[str, object]:
        """API返却用の辞書形式へ変換する。"""

        return {
            "id": self.id,
            "name": self.name,
            "imageCount": self.image_count,
        }


@dataclass(frozen=True)
class MasterMaintenanceSearchResult:
    """マスタメンテナンス候補検索結果を表す。"""

    items: list[MasterMaintenanceItem]
    total_count: int
    limit: int

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "items": [item.to_dict() for item in self.items],
            "totalCount": self.total_count,
            "limit": self.limit,
        }


@dataclass(frozen=True)
class MasterDeleteResult:
    """マスタ削除処理の結果を表す。"""

    id: int
    name: str
    affected_image_count: int
    deleted_count: int

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "id": self.id,
            "name": self.name,
            "affectedImageCount": self.affected_image_count,
            "deletedCount": self.deleted_count,
        }


@dataclass(frozen=True)
class MasterReplaceResult:
    """マスタ置き換え処理の結果を表す。"""

    source_id: int
    source_name: str
    target_id: int
    target_name: str
    affected_image_count: int
    merged: bool

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "sourceId": self.source_id,
            "sourceName": self.source_name,
            "targetId": self.target_id,
            "targetName": self.target_name,
            "affectedImageCount": self.affected_image_count,
            "merged": self.merged,
        }


@dataclass(frozen=True)
class MasterBulkDeleteResult:
    """未使用マスタ一括削除処理の結果を表す。"""

    deleted_count: int

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "deletedCount": self.deleted_count,
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
    model_target_count: int = 0
    model_processed_count: int = 0
    model_linked_count: int = 0
    model_skipped_count: int = 0
    model_failed_count: int = 0

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "targetCount": self.target_count,
            "processedCount": self.processed_count,
            "taggedCount": self.tagged_count,
            "skippedCount": self.skipped_count,
            "failedCount": self.failed_count,
            "modelTargetCount": self.model_target_count,
            "modelProcessedCount": self.model_processed_count,
            "modelLinkedCount": self.model_linked_count,
            "modelSkippedCount": self.model_skipped_count,
            "modelFailedCount": self.model_failed_count,
            "failedFiles": [
                item.to_dict()
                for item in self.failed_files[:20]
            ],
        }


@dataclass(frozen=True)
class CatalogRemovalFailure:
    """管理対象除外で失敗した画像1件分を表す。"""

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
class CatalogRemovalResult:
    """画像の管理対象除外処理結果を表す。"""

    target_count: int
    removed_count: int
    deleted_thumbnail_count: int
    failed_count: int
    failed_files: list[CatalogRemovalFailure]

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "targetCount": self.target_count,
            "removedCount": self.removed_count,
            "deletedThumbnailCount": self.deleted_thumbnail_count,
            "failedCount": self.failed_count,
            "failedFiles": [
                item.to_dict()
                for item in self.failed_files[:20]
            ],
        }


@dataclass(frozen=True)
class TrashMoveFailure:
    """ごみ箱移動で失敗した画像1件分を表す。"""

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
class TrashMoveResult:
    """画像ファイルのごみ箱移動処理結果を表す。"""

    target_count: int
    trashed_count: int
    removed_count: int
    deleted_thumbnail_count: int
    failed_count: int
    failed_files: list[TrashMoveFailure]

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "targetCount": self.target_count,
            "trashedCount": self.trashed_count,
            "removedCount": self.removed_count,
            "deletedThumbnailCount": self.deleted_thumbnail_count,
            "failedCount": self.failed_count,
            "failedFiles": [
                item.to_dict()
                for item in self.failed_files[:20]
            ],
        }


@dataclass(frozen=True)
class ImageRenameResult:
    """画像ファイル名変更処理結果を表す。"""

    id: int
    filename: str
    path: str
    folder: str

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "id": self.id,
            "filename": self.filename,
            "path": self.path,
            "folder": self.folder,
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
class WildcardExportResult:
    """ワイルドカードテキスト出力処理の結果を表す。"""

    path: str
    mode: str
    line_count: int
    cancelled: bool = False

    def to_api_data(self) -> dict[str, object]:
        """Vueへ返却するAPIレスポンス用のデータ形式に変換する。"""

        return {
            "path": self.path,
            "mode": self.mode,
            "lineCount": self.line_count,
            "cancelled": self.cancelled,
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
