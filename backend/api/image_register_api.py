from __future__ import annotations

from typing import Any

from .api_response import ApiResponse
from .service_manager import ServiceManager


class ImageRegisterApi:
    """画像登録系APIを提供する。"""

    def __init__(self, service_manager: ServiceManager) -> None:
        """利用するサービス管理を保持する。"""

        self._service_manager = service_manager

    def import_selected_items(self, payload: dict[str, Any]) -> dict[str, Any]:
        """選択またはドロップされたファイル情報を画像データとして登録する。"""

        result = self._service_manager.import_service.import_items(payload)
        return ApiResponse(
            success=result.success,
            message=result.message,
            data=result.to_api_data(),
        ).to_dict()

    def select_files_dialog(self) -> dict[str, Any]:
        """ネイティブファイル選択ダイアログを開き、選択結果を返す。"""

        try:
            items = self._service_manager.dialog_service.select_files()
            return ApiResponse(success=True, message="", data={"items": items}).to_dict()
        except Exception as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()

    def select_folder_dialog(self) -> dict[str, Any]:
        """ネイティブフォルダ選択ダイアログを開き、選択結果を返す。"""

        try:
            items = self._service_manager.dialog_service.select_folder()
            return ApiResponse(success=True, message="", data={"items": items}).to_dict()
        except Exception as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()
