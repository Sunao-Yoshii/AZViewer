from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Any

from backend.repositories import ImageFileRepository
from backend.services import ImageMetadataService, TagNormalizeService, ThumbnailCacheService

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

    def _normalize_detail_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        """詳細更新ペイロードをリポジトリ用の値へ正規化する。"""

        return {
            "record_id": int(data.get("id")),
            "rating": str(data.get("rating") or ""),
            "is_checked": int(data.get("is_checked")),
            "is_favorite": int(data.get("is_favorite")),
            "comment": self._normalize_detail_comment(data.get("comment")),
        }

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
