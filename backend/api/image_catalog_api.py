from __future__ import annotations

import base64
import logging
import mimetypes
import shutil
from pathlib import Path
from typing import Any

from backend.repositories import ImageFileRepository
from backend.models import (
    BulkTagAddResult,
    BulkAttributeUpdateResult,
    CaptionTagImportResult,
    CatalogRemovalResult,
    FileMoveFailure,
    FileMoveResult,
    ImageFileListItem,
    ImageRenameResult,
    MasterMaintenanceSearchResult,
    PromptTagImportResult,
    TagCaptionExportResult,
    TrashMoveFailure,
    TrashMoveResult,
    WildcardExportResult,
)
from backend.services import (
    BulkTagAddService,
    CaptionTagImportService,
    DialogService,
    ImageMetadataService,
    PromptTagImportService,
    TagCaptionExportService,
    TagNormalizeService,
    ThumbnailCacheService,
    WildcardExportService,
)

from .api_response import ApiResponse
from .database_lifecycle_manager import DatabaseLifecycleManager

LOGGER = logging.getLogger(__name__)


class ImageCatalogApi:
    """画像一覧表示・検索・更新系APIを提供する。"""

    _ALLOWED_PAGE_SIZES = {25, 50, 75, 100, 200, 500, 1000, 2500}
    _DEFAULT_PAGE_SIZE = 25

    def __init__(
        self,
        database_lifecycle_manager: DatabaseLifecycleManager,
        thumbnail_cache_service: ThumbnailCacheService,
        metadata_service: ImageMetadataService | None = None,
        tag_normalize_service: TagNormalizeService | None = None,
        dialog_service: DialogService | None = None,
    ) -> None:
        """利用するDB接続管理と一覧用リポジトリを保持する。"""

        self._database_lifecycle_manager = database_lifecycle_manager
        self._thumbnail_cache_service = thumbnail_cache_service
        self._metadata_service = metadata_service or ImageMetadataService()
        self._tag_normalize_service = tag_normalize_service or TagNormalizeService()
        self._dialog_service = dialog_service
        self._repository: ImageFileRepository | None = None
        self._tag_caption_export_service: TagCaptionExportService | None = None
        self._wildcard_export_service: WildcardExportService | None = None

    def search_image_files(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """画像一覧検索およびページング取得を行う。"""

        data = payload if isinstance(payload, dict) else {}
        tag_hash, tag_set = self._normalize_tag_hash_condition(data)
        result = self._get_repository().search(
            path=str(data.get("path", "") or ""),
            rating=self._normalize_nullable_string(data.get("rating")),
            is_checked=data.get("is_checked"),
            is_favorite=data.get("is_favorite"),
            tags=self._normalize_search_tags(data.get("tags")),
            folder_id=self._normalize_search_folder_id(data.get("folderId")),
            model=self._normalize_search_model(data.get("model")),
            tag_hash=tag_hash,
            tag_set=tag_set,
            tag_keyword=self._normalize_search_tag_keyword(data.get("tag_keyword")),
            page=self._normalize_page(data.get("page")),
            page_size=self._normalize_page_size(data.get("page_size")),
            sort=str(data.get("sort", "id_desc") or "id_desc"),
        )
        return ApiResponse(
            success=True,
            message="Image files loaded.",
            data=result.to_dict(),
        ).to_dict()

    def update_image_file_detail(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """指定レコードの詳細項目を一括更新する。"""

        data = payload if isinstance(payload, dict) else {}
        try:
            detail = self._normalize_detail_payload(data)
            tags = self._tag_normalize_service.normalize_tags(data.get("tags"))
            model_name = self._normalize_model_name(data.get("modelName"))
            updated = self._update_detail_with_tags_and_model(detail, tags, model_name)
        except (TypeError, ValueError) as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()
        except Exception as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()

        if not updated:
            return ApiResponse(success=False, message="対象データが存在しません。", data=None).to_dict()

        return ApiResponse(
            success=True,
            message="Image file detail updated.",
            data={**detail, "tags": tags, "modelName": model_name},
        ).to_dict()

    def bulk_update_image_file_attributes(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """指定レコード群の画像属性を一括更新する。"""

        try:
            data = payload if isinstance(payload, dict) else {}
            record_ids = self._normalize_record_ids(data.get("ids"))
            if not record_ids:
                return ApiResponse(
                    success=False,
                    message="更新対象が指定されていません。",
                    data=self._empty_bulk_attribute_update_data(),
                ).to_dict()

            try:
                updates = self._normalize_bulk_attribute_updates(data.get("updates"))
            except ValueError as exc:
                return ApiResponse(
                    success=False,
                    message=str(exc),
                    data=self._empty_bulk_attribute_update_data(),
                ).to_dict()

            if not updates:
                return ApiResponse(
                    success=False,
                    message="更新項目が指定されていません。",
                    data=self._empty_bulk_attribute_update_data(),
                ).to_dict()

            updated_count = self._get_repository().bulk_update_attributes(
                record_ids=record_ids,
                updates=updates,
            )
            result = BulkAttributeUpdateResult(
                target_count=len(record_ids),
                updated_count=updated_count,
            )
            return ApiResponse(
                success=True,
                message="選択画像の属性を更新しました。",
                data=result.to_api_data(),
            ).to_dict()
        except Exception:
            return ApiResponse(
                success=False,
                message="選択画像の属性更新に失敗しました。",
                data=self._empty_bulk_attribute_update_data(),
            ).to_dict()

    def remove_image_files_from_catalog(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """指定レコード群を実ファイルに触れず管理対象から除外する。"""

        try:
            data = payload if isinstance(payload, dict) else {}
            record_ids = self._normalize_record_ids(data.get("ids"))
            if not record_ids:
                return ApiResponse(
                    success=False,
                    message="除外対象が指定されていません。",
                    data=self._empty_catalog_removal_data(),
                ).to_dict()

            repository = self._get_repository()
            result = self._remove_ids_from_catalog(repository, record_ids)
            return ApiResponse(
                success=True,
                message="選択画像を管理対象から除外しました。",
                data=result.to_api_data(),
            ).to_dict()
        except Exception:
            return ApiResponse(
                success=False,
                message="管理対象からの除外に失敗しました。",
                data=self._empty_catalog_removal_data(),
            ).to_dict()

    def move_image_files_to_trash(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """指定レコード群の実ファイルをごみ箱へ移動し、成功分を管理対象から除外する。"""

        try:
            data = payload if isinstance(payload, dict) else {}
            record_ids = self._normalize_record_ids(data.get("ids"))
            if not record_ids:
                return ApiResponse(
                    success=False,
                    message="ごみ箱へ移動する対象が指定されていません。",
                    data=self._empty_trash_move_data(),
                ).to_dict()

            repository = self._get_repository()
            items = repository.find_by_ids(record_ids)
            result = self._move_items_to_trash_and_remove(repository, items, len(record_ids))
            message = (
                "一部画像をごみ箱へ移動できませんでした。"
                if result.failed_count > 0
                else "選択画像をごみ箱へ移動しました。"
            )
            return ApiResponse(success=True, message=message, data=result.to_api_data()).to_dict()
        except Exception:
            LOGGER.exception("Failed to move image files to trash.")
            return ApiResponse(
                success=False,
                message="ごみ箱への移動に失敗しました。",
                data=self._empty_trash_move_data(),
            ).to_dict()

    def rename_image_file(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """指定レコードの実ファイル名とDB登録情報を変更する。"""

        try:
            data = payload if isinstance(payload, dict) else {}
            record_id = self._normalize_required_record_id(data.get("id"))
            filename = self._normalize_rename_filename(data.get("filename"))
            repository = self._get_repository()
            item = self._find_single_item(repository, record_id)
            result = self._rename_file_and_update_record(repository, item, filename)
            return ApiResponse(
                success=True,
                message="ファイル名を変更しました。",
                data=result.to_api_data(),
            ).to_dict()
        except ValueError as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()
        except Exception:
            LOGGER.exception("Failed to rename image file.")
            return ApiResponse(
                success=False,
                message="ファイル名を変更できませんでした。",
                data=None,
            ).to_dict()

    def move_image_files_to_folder(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """指定レコードの実ファイルを指定フォルダへ一括移動する。"""

        try:
            data = payload if isinstance(payload, dict) else {}
            record_ids = self._normalize_record_ids(data.get("ids"))
            if not record_ids:
                return ApiResponse(
                    success=False,
                    message="移動対象が指定されていません。",
                    data=self._empty_file_move_data(),
                ).to_dict()

            try:
                destination_folder = self._normalize_destination_folder(data.get("destinationFolder"))
            except ValueError as exc:
                return ApiResponse(
                    success=False,
                    message=str(exc),
                    data=self._empty_file_move_data(),
                ).to_dict()

            repository = self._get_repository()
            items = repository.find_by_ids(record_ids)
            result = self._move_files_and_update_records(repository, items, destination_folder)
            message = (
                "一部画像ファイルの移動に失敗しました。"
                if result.failed_count > 0
                else "画像ファイルの移動が完了しました。"
            )
            return ApiResponse(success=True, message=message, data=result.to_api_data()).to_dict()
        except Exception:
            return ApiResponse(
                success=False,
                message="画像ファイルの移動に失敗しました。",
                data=self._empty_file_move_data(),
            ).to_dict()

    def export_selected_image_tags(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """指定レコードのタグを画像ごとのcaptionファイルへ出力する。"""

        try:
            data = payload if isinstance(payload, dict) else {}
            record_ids = self._normalize_record_ids(data.get("ids"))
            if not record_ids:
                return ApiResponse(
                    success=False,
                    message="タグ出力対象が指定されていません。",
                    data=self._empty_tag_caption_export_data(),
                ).to_dict()

            repository = self._get_repository()
            items = repository.find_by_ids(record_ids)
            if not items:
                return ApiResponse(
                    success=True,
                    message="タグ出力対象の画像はありませんでした。",
                    data=self._empty_tag_caption_export_data(),
                ).to_dict()

            tags_by_image_id = repository.find_tags_by_image_ids([item.id for item in items])
            result = self._get_tag_caption_export_service().export(
                items=items,
                tags_by_image_id=tags_by_image_id,
            )
            message = (
                "タグ出力が完了しましたが、一部失敗しました。"
                if result.failed_count > 0
                else "タグ出力が完了しました。"
            )
            return ApiResponse(success=True, message=message, data=result.to_api_data()).to_dict()
        except Exception:
            return ApiResponse(
                success=False,
                message="タグ出力に失敗しました。",
                data=self._empty_tag_caption_export_data(),
            ).to_dict()

    def fetchLocalImage(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """ローカル画像の本体を表示用データURLとして返す。"""

        data = payload if isinstance(payload, dict) else {}
        path = Path(str(data.get("path") or "")).expanduser()
        if not path.is_file():
            return ApiResponse(success=False, message="Image file was not found.", data=None).to_dict()

        binary = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(binary).decode("ascii")
        return ApiResponse(
            success=True,
            message="Image loaded.",
            data={
                "path": str(path),
                "contentType": content_type,
                "dataUrl": f"data:{content_type};base64,{encoded}",
            },
        ).to_dict()

    def fetchLocalImageThumb(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """ローカル画像の表示用データURLを返す。"""
        data = payload if isinstance(payload, dict) else {}
        try:
            record_id = int(data.get("id"))
        except (TypeError, ValueError):
            return ApiResponse(success=False, message="id is required.", data=None).to_dict()

        binary = self._thumbnail_cache_service.get_thumbnail_bytes(record_id)
        if binary is None:
            return ApiResponse(success=False, message="Image file was not found.", data=None).to_dict()
        encoded = base64.b64encode(binary).decode("ascii")
        return ApiResponse(
            success=True,
            message="Image thumbnail loaded.",
            data={
                "id": record_id,
                "contentType": "image/png",
                "dataUrl": f"data:image/png;base64,{encoded}",
            },
        ).to_dict()

    def fetch_image_metadata(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """ローカル画像のメタ情報を表示用テキストとして返す。"""

        data = payload if isinstance(payload, dict) else {}
        path = str(data.get("path") or "")
        if not path:
            return ApiResponse(
                success=False,
                message="path が指定されていません。",
                data={"metadata": ""},
            ).to_dict()

        try:
            metadata = self._metadata_service.fetch_metadata_text(path)
        except FileNotFoundError:
            return ApiResponse(
                success=False,
                message="画像ファイルが存在しません。",
                data={"metadata": ""},
            ).to_dict()
        except Exception:
            return ApiResponse(
                success=False,
                message="メタ情報を取得できませんでした。",
                data={"metadata": ""},
            ).to_dict()

        return ApiResponse(
            success=True,
            message="",
            data={"metadata": metadata},
        ).to_dict()

    def fetch_tags_for_search(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """タグ検索ダイアログに表示するタグ候補を返す。"""

        limit = 256
        try:
            data = payload if isinstance(payload, dict) else {}
            keyword = str(data.get("keyword") or "").strip()
            limit = self._normalize_tag_search_limit(data.get("limit"))
            repository = self._get_repository()
            tags = repository.find_tags_for_search(keyword=keyword, limit=limit)
            total_count = repository.count_tags_for_search(keyword=keyword)
        except Exception:
            return ApiResponse(
                success=False,
                message="タグ一覧を取得できませんでした。",
                data={
                    "tags": [],
                    "total_count": 0,
                    "limit": limit,
                },
            ).to_dict()

        return ApiResponse(
            success=True,
            message="",
            data={
                "tags": [tag.to_dict() for tag in tags],
                "total_count": total_count,
                "limit": limit,
            },
        ).to_dict()

    def fetch_folders_for_search(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """フォルダ検索ダイアログに表示するフォルダ候補を返す。"""

        limit = 256
        try:
            data = payload if isinstance(payload, dict) else {}
            keyword = str(data.get("keyword") or "").strip()
            limit = self._normalize_tag_search_limit(data.get("limit"))
            repository = self._get_repository()
            folders = repository.find_folders_for_search(keyword=keyword, limit=limit)
            total_count = repository.count_folders_for_search(keyword=keyword)
        except Exception:
            return ApiResponse(
                success=False,
                message="フォルダ一覧を取得できませんでした。",
                data={
                    "folders": [],
                    "totalCount": 0,
                    "limit": limit,
                },
            ).to_dict()

        return ApiResponse(
            success=True,
            message="",
            data={
                "folders": [folder.to_dict() for folder in folders],
                "totalCount": total_count,
                "limit": limit,
            },
        ).to_dict()

    def fetch_models_for_search(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """モデル検索ダイアログに表示するモデル候補を返す。"""

        limit = 256
        try:
            data = payload if isinstance(payload, dict) else {}
            keyword = str(data.get("keyword") or "").strip()
            limit = self._normalize_model_search_limit(data.get("limit"))
            repository = self._get_repository()
            models = repository.find_models_for_search(keyword=keyword, limit=limit)
            total_count = repository.count_models_for_search(keyword=keyword)
        except Exception:
            return ApiResponse(
                success=False,
                message="モデル一覧を取得できませんでした。",
                data={
                    "models": [],
                    "total_count": 0,
                    "limit": limit,
                },
            ).to_dict()

        return ApiResponse(
            success=True,
            message="",
            data={
                "models": [model.to_dict() for model in models],
                "total_count": total_count,
                "limit": limit,
            },
        ).to_dict()

    def fetch_tags_for_maintenance(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """タグメンテナンス候補を使用件数付きで返す。"""

        return self._fetch_master_maintenance_items(payload, "tag")

    def fetch_models_for_maintenance(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """モデルメンテナンス候補を使用件数付きで返す。"""

        return self._fetch_master_maintenance_items(payload, "model")

    def fetch_folders_for_maintenance(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """フォルダメンテナンス候補を使用件数付きで返す。"""

        limit = 50
        try:
            data = payload if isinstance(payload, dict) else {}
            keyword = str(data.get("keyword") or "").strip()
            limit = self._normalize_master_maintenance_limit(data.get("limit"))
            repository = self._get_repository()
            folders = repository.find_folders_for_maintenance(keyword=keyword, limit=limit)
            total_count = repository.count_folders_for_maintenance(keyword=keyword)
        except Exception:
            return ApiResponse(
                success=False,
                message="フォルダ一覧を取得できませんでした。",
                data={
                    "items": [],
                    "totalCount": 0,
                    "limit": limit,
                },
            ).to_dict()

        return ApiResponse(
            success=True,
            message="",
            data={
                "items": [folder.to_dict() for folder in folders],
                "totalCount": total_count,
                "limit": limit,
            },
        ).to_dict()

    def delete_tag_master(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """タグマスタを削除し、紐づく画像から解除する。"""

        try:
            tag_id = self._normalize_master_id(payload)
            result = self._get_repository().delete_tag_master(tag_id)
            return ApiResponse(
                success=True,
                message="タグを削除しました。",
                data=result.to_api_data(),
            ).to_dict()
        except ValueError as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()
        except Exception:
            return ApiResponse(success=False, message="タグの削除に失敗しました。", data=None).to_dict()

    def replace_tag_master(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """タグマスタ名を変更または既存タグへ統合する。"""

        try:
            tag_id = self._normalize_master_id(payload)
            new_name = self._normalize_replacement_tag_name(payload)
            result = self._get_repository().replace_tag_master(tag_id, new_name)
            return ApiResponse(
                success=True,
                message="タグを置き換えました。",
                data=result.to_api_data(),
            ).to_dict()
        except ValueError as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()
        except Exception:
            return ApiResponse(success=False, message="タグの置き換えに失敗しました。", data=None).to_dict()

    def delete_unused_tags(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """未使用タグマスタを一括削除する。"""

        try:
            result = self._get_repository().delete_unused_tags()
            return ApiResponse(
                success=True,
                message="未使用タグを削除しました。",
                data=result.to_api_data(),
            ).to_dict()
        except Exception:
            return ApiResponse(success=False, message="未使用タグの削除に失敗しました。", data=None).to_dict()

    def delete_model_master(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """モデルマスタを削除し、紐づく画像から解除する。"""

        try:
            model_id = self._normalize_master_id(payload)
            result = self._get_repository().delete_model_master(model_id)
            return ApiResponse(
                success=True,
                message="モデルを削除しました。",
                data=result.to_api_data(),
            ).to_dict()
        except ValueError as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()
        except Exception:
            return ApiResponse(success=False, message="モデルの削除に失敗しました。", data=None).to_dict()

    def replace_model_master(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """モデルマスタ名を変更または既存モデルへ統合する。"""

        try:
            model_id = self._normalize_master_id(payload)
            new_name = self._normalize_replacement_model_name(payload)
            result = self._get_repository().replace_model_master(model_id, new_name)
            return ApiResponse(
                success=True,
                message="モデルを置き換えました。",
                data=result.to_api_data(),
            ).to_dict()
        except ValueError as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()
        except Exception:
            return ApiResponse(success=False, message="モデルの置き換えに失敗しました。", data=None).to_dict()

    def delete_unused_models(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """未使用モデルマスタを一括削除する。"""

        try:
            result = self._get_repository().delete_unused_models()
            return ApiResponse(
                success=True,
                message="未使用モデルを削除しました。",
                data=result.to_api_data(),
            ).to_dict()
        except Exception:
            return ApiResponse(success=False, message="未使用モデルの削除に失敗しました。", data=None).to_dict()

    def delete_unused_folders(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """未使用フォルダマスタを一括削除する。"""

        try:
            result = self._get_repository().delete_unused_folders()
            return ApiResponse(
                success=True,
                message="未使用フォルダを削除しました。",
                data=result.to_api_data(),
            ).to_dict()
        except Exception:
            return ApiResponse(
                success=False,
                message="未使用フォルダの削除に失敗しました。",
                data={"deletedCount": 0},
            ).to_dict()

    def fetch_duplicate_tag_sets(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """重複しているタグ構成一覧を返す。"""

        limit = 256
        try:
            data = payload if isinstance(payload, dict) else {}
            limit = self._normalize_tag_search_limit(data.get("limit"))
            repository = self._get_repository()
            items = repository.find_duplicate_tag_sets(limit)
            total_count = repository.count_duplicate_tag_sets()
        except Exception:
            return ApiResponse(
                success=False,
                message="重複タグ構成一覧を取得できませんでした。",
                data={
                    "items": [],
                    "totalCount": 0,
                    "limit": limit,
                },
            ).to_dict()

        return ApiResponse(
            success=True,
            message="",
            data={
                "items": [item.to_dict() for item in items],
                "totalCount": total_count,
                "limit": limit,
            },
        ).to_dict()

    def import_prompt_tags(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """タグ未登録画像へプロンプト由来タグを一括登録する。"""

        try:
            result = PromptTagImportService(
                self._get_repository(),
                self._metadata_service,
                self._tag_normalize_service,
            ).import_prompt_tags()
        except Exception:
            result = PromptTagImportResult(
                target_count=0,
                processed_count=0,
                tagged_count=0,
                skipped_count=0,
                failed_count=0,
                failed_files=[],
            )
            return ApiResponse(
                success=False,
                message="プロンプト情報の読み取り中にエラーが発生しました。",
                data=result.to_api_data(),
            ).to_dict()

        return ApiResponse(
            success=True,
            message="プロンプト情報の読み取りが完了しました。",
            data=result.to_api_data(),
        ).to_dict()

    def import_caption_tags(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """指定画像と同名のcaptionファイルからタグを追加登録する。"""

        try:
            data = payload if isinstance(payload, dict) else {}
            record_ids = self._normalize_record_ids(data.get("ids"))
            if not record_ids:
                return ApiResponse(
                    success=False,
                    message="captionタグ読み込み対象が指定されていません。",
                    data=self._empty_caption_tag_import_data(),
                ).to_dict()

            result = CaptionTagImportService(
                self._get_repository(),
                self._tag_normalize_service,
            ).import_caption_tags(record_ids)
            message = (
                "キャプションタグ読み込みが完了しましたが、一部失敗しました。"
                if result.failed_count > 0
                else "キャプションタグ読み込みが完了しました。"
            )
            return ApiResponse(success=True, message=message, data=result.to_api_data()).to_dict()
        except Exception:
            return ApiResponse(
                success=False,
                message="キャプションタグ読み込みに失敗しました。",
                data=self._empty_caption_tag_import_data(),
            ).to_dict()

    def bulk_add_tags(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """指定画像群へ同一タグを追加登録する。"""

        try:
            data = payload if isinstance(payload, dict) else {}
            record_ids = self._normalize_record_ids(data.get("ids"))
            if not record_ids:
                return ApiResponse(
                    success=False,
                    message="タグ追加対象が指定されていません。",
                    data=self._empty_bulk_tag_add_data(),
                ).to_dict()

            tags_text = str(data.get("tagsText") or "")
            result = BulkTagAddService(
                self._get_repository(),
                self._tag_normalize_service,
            ).bulk_add_tags(record_ids, tags_text)
            message = (
                "一括タグ追加が完了しましたが、一部失敗しました。"
                if result.failed_count > 0
                else "一括タグ追加が完了しました。"
            )
            return ApiResponse(success=True, message=message, data=result.to_api_data()).to_dict()
        except ValueError as exc:
            return ApiResponse(
                success=False,
                message=str(exc),
                data=self._empty_bulk_tag_add_data(),
            ).to_dict()
        except Exception:
            return ApiResponse(
                success=False,
                message="一括タグ追加に失敗しました。",
                data=self._empty_bulk_tag_add_data(),
            ).to_dict()

    def export_wildcard_text(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """ワイルドカード出力テキストを保存または追記する。"""

        try:
            data = payload if isinstance(payload, dict) else {}
            mode = str(data.get("mode") or "").strip()
            text = str(data.get("text") or "")
            result = self._get_wildcard_export_service().export_text(mode=mode, text=text)

            if result.cancelled:
                return ApiResponse(
                    success=False,
                    message="保存がキャンセルされました。",
                    data=result.to_api_data(),
                ).to_dict()

            return ApiResponse(
                success=True,
                message="ワイルドカードを出力しました。",
                data=result.to_api_data(),
            ).to_dict()
        except ValueError as exc:
            return ApiResponse(
                success=False,
                message=str(exc),
                data=self._empty_wildcard_export_data(),
            ).to_dict()
        except Exception:
            return ApiResponse(
                success=False,
                message="ワイルドカード出力に失敗しました。",
                data=self._empty_wildcard_export_data(),
            ).to_dict()

    def _get_repository(self) -> ImageFileRepository:
        """一覧系処理で利用するリポジトリを返す。"""

        if self._repository is not None:
            return self._repository

        engine = self._database_lifecycle_manager.get_engine()
        self._repository = ImageFileRepository(engine)
        self._repository.create_table()
        return self._repository

    def _get_wildcard_export_service(self) -> WildcardExportService:
        """ワイルドカード出力サービスを返す。"""

        if self._wildcard_export_service is not None:
            return self._wildcard_export_service
        if self._dialog_service is None:
            raise ValueError("DialogService が初期化されていません。")

        self._wildcard_export_service = WildcardExportService(self._dialog_service)
        return self._wildcard_export_service

    def _get_tag_caption_export_service(self) -> TagCaptionExportService:
        """タグcaption出力サービスを返す。"""

        if self._tag_caption_export_service is None:
            self._tag_caption_export_service = TagCaptionExportService()
        return self._tag_caption_export_service

    def _normalize_nullable_string(self, value: object) -> str | None:
        """未指定文字列をNoneへ正規化する。"""

        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _normalize_page(self, value: object) -> int:
        """検索ページ番号を1以上の整数へ正規化する。"""

        try:
            page = int(value or 1)
        except (TypeError, ValueError):
            return 1
        return max(1, page)

    def _normalize_page_size(self, value: object) -> int:
        """検索ページサイズを許可リスト内の値へ正規化する。"""

        try:
            page_size = int(value or self._DEFAULT_PAGE_SIZE)
        except (TypeError, ValueError):
            return self._DEFAULT_PAGE_SIZE

        if page_size not in self._ALLOWED_PAGE_SIZES:
            return self._DEFAULT_PAGE_SIZE
        return page_size

    def _normalize_search_tags(self, value: object) -> list[str]:
        """検索条件用タグを空文字・重複除去し、最大3件へ丸める。"""

        if not isinstance(value, list):
            return []

        tags: list[str] = []
        for item in value:
            tag = str(item or "").strip()
            if not tag or tag in tags:
                continue
            tags.append(tag)
        return tags[:3]

    def _normalize_search_folder_id(self, value: object) -> int | None:
        """検索条件用フォルダIDを正の整数またはNoneへ正規化する。"""

        if value in (None, ""):
            return None

        try:
            folder_id = int(value)
        except (TypeError, ValueError):
            return None
        return folder_id if folder_id > 0 else None

    def _normalize_search_model(self, value: object) -> str | None:
        """検索条件用モデル名を空文字ならNoneへ正規化する。"""

        model = str(value or "").strip()
        return model or None

    def _normalize_search_tag_keyword(self, value: object) -> str | None:
        """タグ部分一致検索キーワードを小文字化し、空文字ならNoneへ正規化する。"""

        keyword = str(value or "").strip().lower()
        return keyword or None

    def _normalize_tag_hash_condition(self, data: dict[str, Any]) -> tuple[str | None, str | None]:
        """タグ構成検索条件をhashとtag_setが揃う場合だけ有効化する。"""

        tag_hash = str(data.get("tag_hash") or "").strip()
        tag_set = str(data.get("tag_set") or "").strip()
        if not tag_hash or not tag_set:
            return None, None
        return tag_hash, tag_set

    def _normalize_tag_search_limit(self, value: object) -> int:
        """タグ候補取得件数を1から256の範囲へ丸める。"""

        try:
            limit = int(value or 256)
        except (TypeError, ValueError):
            limit = 256
        return max(1, min(limit, 256))

    def _normalize_model_search_limit(self, value: object) -> int:
        """モデル候補取得件数を1から256の範囲へ丸める。"""

        return self._normalize_tag_search_limit(value)

    def _normalize_master_maintenance_limit(self, value: object) -> int:
        """マスタメンテナンス候補取得件数を1から50の範囲へ丸める。"""

        try:
            limit = int(value or 50)
        except (TypeError, ValueError):
            limit = 50
        return max(1, min(limit, 50))

    def _fetch_master_maintenance_items(
        self,
        payload: dict[str, Any] | None,
        mode: str,
    ) -> dict[str, Any]:
        """タグまたはモデルのメンテナンス候補を返す。"""

        limit = 50
        try:
            data = payload if isinstance(payload, dict) else {}
            keyword = str(data.get("keyword") or "").strip()
            limit = self._normalize_master_maintenance_limit(data.get("limit"))
            repository = self._get_repository()
            if mode == "tag":
                items = repository.find_tags_for_maintenance(keyword=keyword, limit=limit)
                total_count = repository.count_tags_for_maintenance(keyword=keyword)
            else:
                items = repository.find_models_for_maintenance(keyword=keyword, limit=limit)
                total_count = repository.count_models_for_maintenance(keyword=keyword)
        except Exception:
            return ApiResponse(
                success=False,
                message="マスタ一覧の取得に失敗しました。",
                data=MasterMaintenanceSearchResult([], 0, limit).to_api_data(),
            ).to_dict()

        return ApiResponse(
            success=True,
            message="",
            data=MasterMaintenanceSearchResult(items, total_count, limit).to_api_data(),
        ).to_dict()

    def _normalize_master_id(self, payload: dict[str, Any] | None) -> int:
        """マスタ操作対象IDを正の整数へ正規化する。"""

        data = payload if isinstance(payload, dict) else {}
        try:
            master_id = int(data.get("id"))
        except (TypeError, ValueError):
            raise ValueError("対象が指定されていません。")
        if master_id <= 0:
            raise ValueError("対象が指定されていません。")
        return master_id

    def _normalize_replacement_tag_name(self, payload: dict[str, Any] | None) -> str:
        """タグ置き換え先名を既存タグ正規化ルールで1件へ正規化する。"""

        data = payload if isinstance(payload, dict) else {}
        tags = self._tag_normalize_service.normalize_tags([data.get("newName")])
        if not tags:
            raise ValueError("タグ名を入力してください。")
        if len(tags) > 1:
            raise ValueError("タグ名は1件だけ指定してください。")
        return tags[0]

    def _normalize_replacement_model_name(self, payload: dict[str, Any] | None) -> str:
        """モデル置き換え先名を保存用表記へ正規化する。"""

        data = payload if isinstance(payload, dict) else {}
        model_name = str(data.get("newName") or "").strip()
        if not model_name:
            raise ValueError("モデル名を入力してください。")
        if len(model_name) > 512:
            raise ValueError("モデル名は512文字以内で入力してください。")
        return model_name

    def _normalize_detail_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        """詳細更新ペイロードをリポジトリ用の値へ正規化する。"""

        return {
            "record_id": int(data.get("id")),
            "rating": str(data.get("rating") or ""),
            "is_checked": int(data.get("is_checked")),
            "is_favorite": int(data.get("is_favorite")),
            "comment": self._normalize_detail_comment(data.get("comment")),
        }

    def _normalize_model_name(self, value: object) -> str | None:
        """詳細保存用モデル名を検証して正規化する。"""

        model_name = str(value or "").strip()
        if not model_name:
            return None
        if len(model_name) > 512:
            raise ValueError("モデル名は512文字以内で入力してください。")
        return model_name

    def _normalize_record_ids(self, value: object) -> list[int]:
        """レコードIDを正の整数の重複なしリストへ正規化する。"""

        if not isinstance(value, list):
            return []

        record_ids: list[int] = []
        for item in value:
            try:
                record_id = int(item)
            except (TypeError, ValueError):
                continue

            if record_id <= 0 or record_id in record_ids:
                continue
            record_ids.append(record_id)
        return record_ids

    def _normalize_required_record_id(self, value: object) -> int:
        """必須レコードIDを正の整数として検証する。"""

        try:
            record_id = int(value)
        except (TypeError, ValueError):
            raise ValueError("id が指定されていません。")

        if record_id <= 0:
            raise ValueError("id が不正です。")
        return record_id

    def _normalize_rename_filename(self, value: object) -> str:
        """リネーム用ファイル名を検証して正規化する。"""

        filename = str(value or "").strip()
        if not filename:
            raise ValueError("ファイル名を入力してください。")
        if any(separator in filename for separator in ("/", "\\")):
            raise ValueError("ファイル名にパス区切り文字は使用できません。")
        if any(char in filename for char in '<>:"|?*'):
            raise ValueError('ファイル名に使用できない文字が含まれています。')
        if Path(filename).name != filename:
            raise ValueError("ファイル名のみを入力してください。")
        if not Path(filename).suffix:
            raise ValueError("拡張子は変更できません。")
        return filename

    def _normalize_bulk_attribute_updates(self, value: object) -> dict[str, object]:
        """一括属性更新ペイロードをリポジトリ用の値へ正規化する。"""

        if not isinstance(value, dict):
            return {}

        updates: dict[str, object] = {}
        if "rating" in value:
            rating = str(value.get("rating") or "").strip()
            if rating not in ("General", "R-15", "R-18", "R-18G"):
                raise ValueError("不正なレーティングが指定されています。")
            updates["rating"] = rating

        if "isChecked" in value:
            updates["is_checked"] = self._normalize_flag_value(value.get("isChecked"))

        if "isFavorite" in value:
            updates["is_favorite"] = self._normalize_flag_value(value.get("isFavorite"))

        return updates

    def _normalize_flag_value(self, value: object) -> int:
        """フラグ値を0または1へ正規化する。"""

        try:
            normalized = int(value)
        except (TypeError, ValueError):
            raise ValueError("不正なフラグ値が指定されています。")

        if normalized not in (0, 1):
            raise ValueError("不正なフラグ値が指定されています。")
        return normalized

    def _normalize_destination_folder(self, value: object) -> Path:
        """移動先フォルダを絶対パス化し、存在するディレクトリか検証する。"""

        folder_text = str(value or "").strip()
        if not folder_text:
            raise ValueError("移動先フォルダが指定されていません。")

        folder_path = Path(folder_text).expanduser().resolve()
        if not folder_path.exists():
            raise ValueError("移動先フォルダが存在しません。")
        if not folder_path.is_dir():
            raise ValueError("移動先がフォルダではありません。")
        return folder_path

    def _empty_catalog_removal_data(self) -> dict[str, object]:
        """管理対象除外API用の空結果データを返す。"""

        return CatalogRemovalResult(
            target_count=0,
            removed_count=0,
            deleted_thumbnail_count=0,
            failed_count=0,
            failed_files=[],
        ).to_api_data()

    def _empty_trash_move_data(self) -> dict[str, object]:
        """ごみ箱移動API用の空結果データを返す。"""

        return TrashMoveResult(
            target_count=0,
            trashed_count=0,
            removed_count=0,
            deleted_thumbnail_count=0,
            failed_count=0,
            failed_files=[],
        ).to_api_data()

    def _empty_file_move_data(self) -> dict[str, object]:
        """一括ファイル移動API用の空結果データを返す。"""

        return FileMoveResult(
            target_count=0,
            moved_count=0,
            skipped_count=0,
            failed_count=0,
            failed_files=[],
        ).to_api_data()

    def _empty_wildcard_export_data(self) -> dict[str, object]:
        """ワイルドカード出力API用の空結果データを返す。"""

        return WildcardExportResult(
            path="",
            mode="",
            line_count=0,
            cancelled=False,
        ).to_api_data()

    def _empty_bulk_attribute_update_data(self) -> dict[str, object]:
        """一括属性更新API用の空結果データを返す。"""

        return BulkAttributeUpdateResult(
            target_count=0,
            updated_count=0,
        ).to_api_data()

    def _empty_tag_caption_export_data(self) -> dict[str, object]:
        """タグcaption出力API用の空結果データを返す。"""

        return TagCaptionExportResult(
            target_count=0,
            exported_count=0,
            skipped_count=0,
            failed_count=0,
            failed_files=[],
        ).to_api_data()

    def _empty_caption_tag_import_data(self) -> dict[str, object]:
        """captionタグ読み込みAPI用の空結果データを返す。"""

        return CaptionTagImportResult(
            target_count=0,
            updated_count=0,
            skipped_count=0,
            failed_count=0,
            failed_files=[],
        ).to_api_data()

    def _empty_bulk_tag_add_data(self) -> dict[str, object]:
        """一括タグ追加API用の空結果データを返す。"""

        return BulkTagAddResult(
            target_count=0,
            updated_count=0,
            skipped_count=0,
            failed_count=0,
            failed_files=[],
        ).to_api_data()

    def _remove_ids_from_catalog(
        self,
        repository: ImageFileRepository,
        record_ids: list[int],
    ) -> CatalogRemovalResult:
        """指定ID群のサムネイルとDB登録情報を削除する。"""

        deleted_thumbnail_count = self._thumbnail_cache_service.delete_thumbnails(record_ids)
        removed_count = repository.remove_from_catalog_by_ids(record_ids)
        return CatalogRemovalResult(
            target_count=len(record_ids),
            removed_count=removed_count,
            deleted_thumbnail_count=deleted_thumbnail_count,
            failed_count=max(0, len(record_ids) - removed_count),
            failed_files=[],
        )

    def _move_items_to_trash_and_remove(
        self,
        repository: ImageFileRepository,
        items: list[ImageFileListItem],
        target_count: int,
    ) -> TrashMoveResult:
        """ごみ箱移動に成功または実ファイル不存在の画像を管理対象から除外する。"""

        trash_plan = self._move_items_to_trash(items)
        removable_ids = trash_plan["removable_ids"]
        removed_count = 0
        deleted_thumbnail_count = 0
        if removable_ids:
            try:
                deleted_thumbnail_count = self._thumbnail_cache_service.delete_thumbnails(removable_ids)
                removed_count = repository.remove_from_catalog_by_ids(removable_ids)
            except Exception:
                LOGGER.exception("Failed to remove trashed image records from catalog.")
                raise

        return TrashMoveResult(
            target_count=target_count,
            trashed_count=trash_plan["trashed_count"],
            removed_count=removed_count,
            deleted_thumbnail_count=deleted_thumbnail_count,
            failed_count=len(trash_plan["failed_files"]),
            failed_files=trash_plan["failed_files"],
        )

    def _move_items_to_trash(self, items: list[ImageFileListItem]) -> dict[str, Any]:
        """画像ファイルをごみ箱へ移動し、管理対象除外へ進めるIDを返す。"""

        removable_ids: list[int] = []
        failed_files: list[TrashMoveFailure] = []
        trashed_count = 0

        for item in items:
            try:
                moved, missing = self._move_file_to_trash(item.path)
                trashed_count += 1 if moved else 0
                if moved or missing:
                    removable_ids.append(item.id)
            except Exception:
                failed_files.append(
                    TrashMoveFailure(
                        id=item.id,
                        path=item.path,
                        reason="ごみ箱へ移動できませんでした。",
                    )
                )

        return {
            "removable_ids": removable_ids,
            "trashed_count": trashed_count,
            "failed_files": failed_files,
        }

    def _move_file_to_trash(self, path: str) -> tuple[bool, bool]:
        """1つの実ファイルをごみ箱へ移動し、移動済みか不存在かを返す。"""

        image_path = Path(path)
        if not image_path.exists():
            return False, True
        if not image_path.is_file():
            raise ValueError("画像ファイルではありません。")

        from send2trash import send2trash

        send2trash(str(image_path))
        return True, False

    def _find_single_item(self, repository: ImageFileRepository, record_id: int) -> ImageFileListItem:
        """指定IDの画像レコードを1件取得する。"""

        items = repository.find_by_ids([record_id])
        if not items:
            raise ValueError("対象データが存在しません。")
        return items[0]

    def _rename_file_and_update_record(
        self,
        repository: ImageFileRepository,
        item: ImageFileListItem,
        filename: str,
    ) -> ImageRenameResult:
        """実ファイルをリネームしてDBのファイル識別情報を更新する。"""

        source_path = Path(item.path)
        destination_path = self._build_rename_destination(source_path, filename)
        source_path.rename(destination_path)
        try:
            updated_count = repository.update_file_identity(
                item.id,
                destination_path.name,
                str(destination_path),
            )
            if updated_count != 1:
                raise RuntimeError("Image file record could not be updated.")
        except Exception:
            self._restore_renamed_file(destination_path, source_path)
            raise

        return ImageRenameResult(
            id=item.id,
            filename=destination_path.name,
            path=str(destination_path),
            folder=destination_path.parent.name,
        )

    def _build_rename_destination(self, source_path: Path, filename: str) -> Path:
        """リネーム先パスを作成し、ファイル名変更ルールを検証する。"""

        if not source_path.exists():
            raise ValueError("対象ファイルが存在しません。")
        if not source_path.is_file():
            raise ValueError("対象が画像ファイルではありません。")
        if filename == source_path.name:
            raise ValueError("現在と同じファイル名です。")

        destination_path = source_path.with_name(filename)
        if destination_path.suffix.lower() != source_path.suffix.lower():
            raise ValueError("拡張子は変更できません。")
        if destination_path.exists():
            raise ValueError("同名ファイルが既に存在します。")
        return destination_path

    def _restore_renamed_file(self, destination_path: Path, source_path: Path) -> None:
        """DB更新失敗時にリネーム済みファイルを元へ戻す。"""

        try:
            if destination_path.exists() and not source_path.exists():
                destination_path.rename(source_path)
        except Exception:
            LOGGER.exception(
                "Failed to restore renamed image file: %s -> %s",
                destination_path,
                source_path,
            )

    def _move_files_and_update_records(
        self,
        repository: ImageFileRepository,
        items: list[ImageFileListItem],
        destination_folder: Path,
    ) -> FileMoveResult:
        """移動可能な実ファイルを移動し、成功分だけDBパスを更新する。"""

        move_plan = self._move_files(repository, items, destination_folder)
        moved_items = move_plan["moved_items"]
        failed_count = move_plan["failed_count"]
        failed_files = move_plan["failed_files"]

        if moved_items:
            try:
                repository.update_paths(self._build_path_updates(moved_items))
            except Exception:
                restored_failures = self._restore_moved_files(moved_items)
                failed_count += len(moved_items)
                failed_files.extend(restored_failures)
                moved_items = []

        return FileMoveResult(
            target_count=len(items),
            moved_count=len(moved_items),
            skipped_count=move_plan["skipped_count"],
            failed_count=failed_count,
            failed_files=failed_files,
        )

    def _move_files(
        self,
        repository: ImageFileRepository,
        items: list[ImageFileListItem],
        destination_folder: Path,
    ) -> dict[str, Any]:
        """各画像ファイルを移動し、DB更新候補と失敗情報を集計する。"""

        moved_items: list[dict[str, object]] = []
        failed_files: list[FileMoveFailure] = []
        failed_count = 0
        skipped_count = 0

        for item in items:
            try:
                moved_item = self._move_one_file(repository, item, destination_folder)
                if moved_item is None:
                    skipped_count += 1
                else:
                    moved_items.append(moved_item)
            except Exception as exc:
                failed_count += 1
                self._append_file_move_failure(failed_files, item.id, item.path, exc)

        return {
            "moved_items": moved_items,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "failed_files": failed_files,
        }

    def _move_one_file(
        self,
        repository: ImageFileRepository,
        item: ImageFileListItem,
        destination_folder: Path,
    ) -> dict[str, object] | None:
        """1画像ファイルを移動し、DB更新候補を返す。同一パスならNoneを返す。"""

        source_path = Path(item.path)
        if not source_path.exists():
            raise FileNotFoundError("移動元ファイルが存在しません。")
        if not source_path.is_file():
            raise ValueError("画像ファイルではありません。")

        destination_path = destination_folder / source_path.name
        if source_path.resolve() == destination_path.resolve():
            return None
        if destination_path.exists():
            raise FileExistsError("移動先に同名ファイルが既に存在します。")
        if repository.exists_by_path(str(destination_path)):
            raise ValueError("移動後パスは既に登録済みです。")

        shutil.move(str(source_path), str(destination_path))
        return {
            "id": item.id,
            "old_path": str(source_path),
            "new_path": str(destination_path),
            "filename": destination_path.name,
            "folder_path": str(destination_path.parent),
            "folder_name": destination_path.parent.name,
        }

    def _build_path_updates(self, moved_items: list[dict[str, object]]) -> list[dict[str, object]]:
        """DBのファイル識別情報更新用ペイロードを作る。"""

        return [
            {
                "id": item["id"],
                "path": item["new_path"],
                "filename": item["filename"],
                "folder_path": item["folder_path"],
                "folder_name": item["folder_name"],
            }
            for item in moved_items
        ]

    def _restore_moved_files(self, moved_items: list[dict[str, object]]) -> list[FileMoveFailure]:
        """DB更新失敗時に移動済みファイルを元へ戻し、失敗情報を返す。"""

        failures: list[FileMoveFailure] = []
        for item in moved_items:
            try:
                new_path = Path(str(item["new_path"]))
                old_path = Path(str(item["old_path"]))
                if new_path.exists() and not old_path.exists():
                    shutil.move(str(new_path), str(old_path))
                self._append_file_move_message(
                    failures,
                    int(item["id"]),
                    str(item["old_path"]),
                    "DB 更新に失敗したため、ファイル移動を取り消しました。",
                )
            except Exception:
                self._append_file_move_message(
                    failures,
                    int(item["id"]),
                    str(item["new_path"]),
                    "DB 更新に失敗し、移動済みファイルの復元にも失敗しました。",
                )
        return failures

    def _append_file_move_failure(
        self,
        failed_files: list[FileMoveFailure],
        record_id: int,
        path: str,
        error: Exception,
    ) -> None:
        """ファイル移動失敗情報を最大20件まで追加する。"""

        self._append_file_move_message(
            failed_files,
            record_id,
            path,
            self._to_file_move_failure_reason(error),
        )

    def _append_file_move_message(
        self,
        failed_files: list[FileMoveFailure],
        record_id: int,
        path: str,
        reason: str,
    ) -> None:
        """ファイル移動失敗メッセージを最大20件まで追加する。"""

        if len(failed_files) >= 20:
            return
        failed_files.append(FileMoveFailure(id=record_id, path=path, reason=reason))

    def _to_file_move_failure_reason(self, error: Exception) -> str:
        """ファイル移動例外をユーザー向け理由へ変換する。"""

        if isinstance(error, FileNotFoundError):
            return "移動元ファイルが存在しません。"
        if isinstance(error, FileExistsError):
            return "移動先に同名ファイルが既に存在します。"
        if isinstance(error, PermissionError):
            return "ファイルへアクセスできません。別のアプリで使用中の可能性があります。"
        if isinstance(error, ValueError):
            return str(error)
        return "ファイルを移動できませんでした。"

    def _update_detail_with_tags_and_model(
        self,
        detail: dict[str, Any],
        tags: list[str],
        model_name: str | None,
    ) -> bool:
        """詳細項目、タグリンク、モデルリンクを同一トランザクションで更新する。"""

        repository = self._get_repository()
        return repository.update_detail_with_tags_and_model(detail, tags, model_name)

    def _normalize_detail_comment(self, value: object) -> str | None:
        """詳細更新コメントをDB保存値へ正規化する。"""

        if value is None:
            return None

        comment = str(value)
        if comment == "":
            return None
        if len(comment) > 255:
            raise ValueError("comment must be 255 characters or less.")
        return comment
