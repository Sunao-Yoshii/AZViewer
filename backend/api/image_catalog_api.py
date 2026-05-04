from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Any

from backend.repositories import ImageFileRepository
from backend.models import PhysicalDeleteFailure, PhysicalDeleteResult, PromptTagImportResult
from backend.services import ImageMetadataService, PromptTagImportService, TagNormalizeService, ThumbnailCacheService

from .api_response import ApiResponse
from .database_lifecycle_manager import DatabaseLifecycleManager


class ImageCatalogApi:
    """画像一覧表示・検索・更新系APIを提供する。"""

    def __init__(
        self,
        database_lifecycle_manager: DatabaseLifecycleManager,
        thumbnail_cache_service: ThumbnailCacheService,
        metadata_service: ImageMetadataService | None = None,
    ) -> None:
        """利用するDB接続管理と一覧用リポジトリを保持する。"""

        self._database_lifecycle_manager = database_lifecycle_manager
        self._thumbnail_cache_service = thumbnail_cache_service
        self._metadata_service = metadata_service or ImageMetadataService()
        self._tag_normalize_service = TagNormalizeService()
        self._repository: ImageFileRepository | None = None

    def search_image_files(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """画像一覧検索およびページング取得を行う。"""

        data = payload if isinstance(payload, dict) else {}
        result = self._get_repository().search(
            path=str(data.get("path", "") or ""),
            rating=self._normalize_nullable_string(data.get("rating")),
            is_checked=data.get("is_checked"),
            is_favorite=data.get("is_favorite"),
            tags=self._normalize_search_tags(data.get("tags")),
            folder=self._normalize_search_folder(data.get("folder")),
            page=int(data.get("page", 1) or 1),
            page_size=int(data.get("page_size", 25) or 25),
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
            updated = self._update_detail_with_tags(detail, tags)
        except (TypeError, ValueError) as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()
        except Exception as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()

        if not updated:
            return ApiResponse(success=False, message="対象データが存在しません。", data=None).to_dict()

        return ApiResponse(
            success=True,
            message="Image file detail updated.",
            data={**detail, "tags": tags},
        ).to_dict()

    def delete_image_file(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """指定レコードを削除し、対応するサムネイルを削除する。"""

        data = payload if isinstance(payload, dict) else {}
        try:
            record_id = int(data.get("id"))
        except (TypeError, ValueError):
            return ApiResponse(success=False, message="id is required.", data=None).to_dict()

        deleted = self._get_repository().delete_by_id(record_id)
        if not deleted:
            return ApiResponse(success=False, message="対象データが存在しません。", data=None).to_dict()

        self._thumbnail_cache_service.delete_thumbnail(record_id)
        return ApiResponse(
            success=True,
            message="Image file deleted.",
            data={"id": record_id},
        ).to_dict()

    def delete_image_files_with_physical_files(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """指定レコードの実ファイル、サムネイル、DBレコードを一括削除する。"""

        try:
            data = payload if isinstance(payload, dict) else {}
            record_ids = self._normalize_delete_ids(data.get("ids"))
            if not record_ids:
                return ApiResponse(
                    success=False,
                    message="削除対象が指定されていません。",
                    data=self._empty_physical_delete_data(),
                ).to_dict()

            repository = self._get_repository()
            items = repository.find_by_ids(record_ids)
            if not items:
                return ApiResponse(
                    success=True,
                    message="削除対象の画像はありませんでした。",
                    data=self._empty_physical_delete_data(),
                ).to_dict()

            result = self._delete_physical_files_and_records(repository, items)
            message = (
                "一部画像の削除に失敗しました。"
                if result.failed_count > 0
                else "選択画像の削除が完了しました。"
            )
            return ApiResponse(success=True, message=message, data=result.to_api_data()).to_dict()
        except Exception:
            return ApiResponse(
                success=False,
                message="選択画像の削除に失敗しました。",
                data=self._empty_physical_delete_data(),
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
                    "total_count": 0,
                    "limit": limit,
                },
            ).to_dict()

        return ApiResponse(
            success=True,
            message="",
            data={
                "folders": [folder.to_dict() for folder in folders],
                "total_count": total_count,
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

    def _get_repository(self) -> ImageFileRepository:
        """一覧系処理で利用するリポジトリを返す。"""

        if self._repository is not None:
            return self._repository

        connection = self._database_lifecycle_manager.get_connection()
        self._repository = ImageFileRepository(connection)
        self._repository.create_table()
        return self._repository

    def _normalize_nullable_string(self, value: object) -> str | None:
        """未指定文字列をNoneへ正規化する。"""

        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

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

    def _normalize_search_folder(self, value: object) -> str | None:
        """検索条件用フォルダを空文字ならNoneへ正規化する。"""

        folder = str(value or "").strip()
        return folder or None

    def _normalize_tag_search_limit(self, value: object) -> int:
        """タグ候補取得件数を1から256の範囲へ丸める。"""

        try:
            limit = int(value or 256)
        except (TypeError, ValueError):
            limit = 256
        return max(1, min(limit, 256))

    def _normalize_detail_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        """詳細更新ペイロードをリポジトリ用の値へ正規化する。"""

        return {
            "record_id": int(data.get("id")),
            "rating": str(data.get("rating") or ""),
            "is_checked": int(data.get("is_checked")),
            "is_favorite": int(data.get("is_favorite")),
            "comment": self._normalize_detail_comment(data.get("comment")),
        }

    def _normalize_delete_ids(self, value: object) -> list[int]:
        """一括削除対象IDを正の整数の重複なしリストへ正規化する。"""

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

    def _empty_physical_delete_data(self) -> dict[str, object]:
        """一括物理削除API用の空結果データを返す。"""

        return PhysicalDeleteResult(
            target_count=0,
            deleted_file_count=0,
            deleted_thumbnail_count=0,
            deleted_record_count=0,
            missing_file_count=0,
            failed_count=0,
            failed_files=[],
        ).to_api_data()

    def _delete_physical_files_and_records(
        self,
        repository: ImageFileRepository,
        items: list,
    ) -> PhysicalDeleteResult:
        """実ファイル削除に成功した画像だけサムネイルとDBレコードを削除する。"""

        delete_plan = self._delete_physical_files(items)
        deletable_ids = delete_plan["deletable_ids"]
        if deletable_ids:
            deleted_thumbnail_count = self._thumbnail_cache_service.delete_thumbnails(deletable_ids)
            deleted_record_count = repository.delete_by_ids(deletable_ids)
        else:
            deleted_thumbnail_count = 0
            deleted_record_count = 0

        return PhysicalDeleteResult(
            target_count=len(items),
            deleted_file_count=delete_plan["deleted_file_count"],
            deleted_thumbnail_count=deleted_thumbnail_count,
            deleted_record_count=deleted_record_count,
            missing_file_count=delete_plan["missing_file_count"],
            failed_count=len(items) - len(deletable_ids),
            failed_files=delete_plan["failed_files"],
        )

    def _delete_physical_files(self, items: list) -> dict[str, Any]:
        """画像ファイルを削除し、DB削除へ進めるIDと失敗情報を返す。"""

        deletable_ids: list[int] = []
        failed_files: list[PhysicalDeleteFailure] = []
        deleted_file_count = 0
        missing_file_count = 0

        for item in items:
            try:
                file_deleted, file_missing = self._delete_physical_file(item.path)
                deleted_file_count += 1 if file_deleted else 0
                missing_file_count += 1 if file_missing else 0
                deletable_ids.append(item.id)
            except Exception:
                if len(failed_files) < 20:
                    failed_files.append(
                        PhysicalDeleteFailure(
                            id=item.id,
                            path=item.path,
                            reason="ファイルを削除できませんでした。",
                        )
                    )

        return {
            "deletable_ids": deletable_ids,
            "deleted_file_count": deleted_file_count,
            "missing_file_count": missing_file_count,
            "failed_files": failed_files,
        }

    def _delete_physical_file(self, path: str) -> tuple[bool, bool]:
        """1つの実ファイルを削除し、削除済みか不存在かを返す。"""

        image_path = Path(path)
        if not image_path.exists():
            return False, True
        if not image_path.is_file():
            raise ValueError("画像ファイルではありません。")

        image_path.unlink()
        return True, False

    def _update_detail_with_tags(self, detail: dict[str, Any], tags: list[str]) -> bool:
        """詳細項目とタグリンクを同一トランザクションで更新する。"""

        connection = self._database_lifecycle_manager.get_connection()
        repository = self._get_repository()
        try:
            connection.execute("BEGIN")
            updated = repository.update_detail(**detail, commit=False)
            if not updated:
                connection.rollback()
                return False
            repository.replace_tags(int(detail["record_id"]), tags)
            connection.commit()
            return True
        except Exception:
            connection.rollback()
            raise

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
