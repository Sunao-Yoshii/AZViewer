from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import webview

from backend.db import ConnectionManager
from backend.repositories import ImageFileRepository
from backend.services import (
    DialogService,
    FileScanService,
    ImageFileImportService,
    StartupCleanupService,
)


@dataclass(frozen=True)
class ApiResponse:
    success: bool
    message: str
    data: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
        }


class AppApi:
    """Public API exposed to Vue through pywebview."""

    def __init__(self) -> None:
        self._connection_manager = ConnectionManager()
        self._repository: ImageFileRepository | None = None
        self._import_service: ImageFileImportService | None = None
        self._cleanup_service: StartupCleanupService | None = None
        self._dialog_service = DialogService(self._get_active_window)

    def initialize_app_backend(self) -> None:
        self._connection_manager.initialize()
        connection = self._connection_manager.get_connection()
        file_scan_service = FileScanService()

        self._repository = ImageFileRepository(connection)
        self._repository.create_table()
        self._import_service = ImageFileImportService(
            connection,
            self._repository,
            file_scan_service,
        )
        self._cleanup_service = StartupCleanupService(connection, self._repository)
        self._cleanup_service.cleanup_missing_files()

    def close(self) -> None:
        self._connection_manager.close()

    def initialize(self) -> dict[str, Any]:
        return self.initialize_app()

    def initialize_app(self) -> dict[str, Any]:
        return ApiResponse(
            success=True,
            message="",
            data={
                "appName": "AZViewer",
                "initialized_at": datetime.now().isoformat(timespec="seconds"),
            },
        ).to_dict()

    def get_app_info(self) -> dict[str, Any]:
        return ApiResponse(
            success=True,
            message="Application information loaded.",
            data={
                "name": "AZViewer",
                "version": "0.1.0",
                "description": "pywebview + Vue + Bootstrap application foundation.",
            },
        ).to_dict()

    def get_menu_definitions(self) -> dict[str, Any]:
        return ApiResponse(
            success=True,
            message="Menu definitions loaded.",
            data=[
                {
                    "key": "home",
                    "label": "Home",
                    "description": "基盤の概要とアプリ情報を表示します。",
                },
                {
                    "key": "sample",
                    "label": "Sample",
                    "description": "今後の機能追加用プレースホルダです。",
                },
            ],
        ).to_dict()

    def health_check(self) -> dict[str, Any]:
        return ApiResponse(
            success=True,
            message="Python API is available.",
            data={
                "status": "ok",
                "checked_at": datetime.now().isoformat(timespec="seconds"),
            },
        ).to_dict()

    def import_selected_items(self, payload: dict[str, Any]) -> dict[str, Any]:
        service = self._get_import_service()
        result = service.import_items(payload)
        return ApiResponse(
            success=result.success,
            message=result.message,
            data=result.to_api_data(),
        ).to_dict()

    def select_files_dialog(self) -> dict[str, Any]:
        try:
            items = self._dialog_service.select_files()
            return ApiResponse(
                success=True,
                message="",
                data={"items": items},
            ).to_dict()
        except Exception as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()

    def select_folder_dialog(self) -> dict[str, Any]:
        try:
            items = self._dialog_service.select_folder()
            return ApiResponse(
                success=True,
                message="",
                data={"items": items},
            ).to_dict()
        except Exception as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()

    def _get_import_service(self) -> ImageFileImportService:
        if self._import_service is None:
            self.initialize_app_backend()
        if self._import_service is None:
            raise RuntimeError("Image file import service is not initialized.")
        return self._import_service

    def _get_active_window(self) -> object | None:
        if not webview.windows:
            return None
        return webview.windows[0]
