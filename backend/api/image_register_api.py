from __future__ import annotations

from typing import Any

from backend.repositories import ImageFileRepository
from backend.services import (
    DialogService,
    FileScanService,
    ImageFileImportService,
    ThumbnailCacheService,
)

from .api_response import ApiResponse
from .service_manager import ServiceManager


class ImageRegisterApi:
    """画像登録系APIを提供する。"""

    def __init__(
        self,
        service_manager: ServiceManager,
        window_provider,
        thumbnail_cache_service: ThumbnailCacheService,
    ) -> None:
        """利用するサービス管理と画像登録系サービスを保持する。"""

        self._service_manager = service_manager
        self._dialog_service = DialogService(window_provider)
        self._thumbnail_cache_service = thumbnail_cache_service
        self._repository: ImageFileRepository | None = None
        self._import_service: ImageFileImportService | None = None

    def _get_import_service(self) -> ImageFileImportService:
        """画像ファイル登録サービスを取得し、未初期化の場合は初期化する。"""

        if self._import_service is not None:
            return self._import_service

        connection = self._service_manager.get_connection()
        self._repository = ImageFileRepository(connection)
        self._repository.create_table()
        self._import_service = ImageFileImportService(
            connection,
            self._repository,
            FileScanService(),
            self._thumbnail_cache_service,
        )
        return self._import_service

    def import_selected_items(self, payload: dict[str, Any]) -> dict[str, Any]:
        """選択またはドロップされたファイル情報を画像データとして登録する。"""

        result = self._get_import_service().import_items(payload)
        return ApiResponse(
            success=result.success,
            message=result.message,
            data=result.to_api_data(),
        ).to_dict()

    def select_files_dialog(self) -> dict[str, Any]:
        """ネイティブファイル選択ダイアログを開き、選択結果を返す。"""

        try:
            items = self._dialog_service.select_files()
            return ApiResponse(success=True, message="", data={"items": items}).to_dict()
        except Exception as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()

    def select_folder_dialog(self) -> dict[str, Any]:
        """ネイティブフォルダ選択ダイアログを開き、選択結果を返す。"""

        try:
            items = self._dialog_service.select_folder()
            return ApiResponse(success=True, message="", data={"items": items}).to_dict()
        except Exception as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()
