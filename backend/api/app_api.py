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
    """Vueへ返却するpywebview APIレスポンスの共通形式を表す。"""

    success: bool
    message: str
    data: Any = None

    def to_dict(self) -> dict[str, Any]:
        """pywebview経由で返却しやすい辞書形式に変換する。"""

        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
        }


class AppApi:
    """pywebviewを通じてVueへ公開するアプリケーションAPIを提供する。"""

    def __init__(self) -> None:
        """APIが利用する各種サービスと遅延初期化用の状態を準備する。"""

        self._connection_manager = ConnectionManager()
        self._repository: ImageFileRepository | None = None
        self._import_service: ImageFileImportService | None = None
        self._cleanup_service: StartupCleanupService | None = None
        self._dialog_service = DialogService(self._get_active_window)

    def initialize_app_backend(self) -> None:
        """データベース、リポジトリ、サービスを初期化する。"""

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
        """アプリケーション終了時に保持している接続を閉じる。"""

        self._connection_manager.close()

    def initialize(self) -> dict[str, Any]:
        """互換用の初期化APIとしてアプリ初期化情報を返す。"""

        return self.initialize_app()

    def initialize_app(self) -> dict[str, Any]:
        """Vue側の起動時に必要な初期化済みアプリ情報を返す。"""

        return ApiResponse(
            success=True,
            message="",
            data={
                "appName": "AZViewer",
                "initialized_at": datetime.now().isoformat(timespec="seconds"),
            },
        ).to_dict()

    def get_app_info(self) -> dict[str, Any]:
        """アプリケーション名やバージョンなどの基本情報を返す。"""

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
        """サイドバーなどで表示するメニュー定義を返す。"""

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
        """Python APIが呼び出し可能か確認するための応答を返す。"""

        return ApiResponse(
            success=True,
            message="Python API is available.",
            data={
                "status": "ok",
                "checked_at": datetime.now().isoformat(timespec="seconds"),
            },
        ).to_dict()

    def import_selected_items(self, payload: dict[str, Any]) -> dict[str, Any]:
        """選択またはドロップされたファイル情報を画像データとして登録する。"""

        service = self._get_import_service()
        result = service.import_items(payload)
        return ApiResponse(
            success=result.success,
            message=result.message,
            data=result.to_api_data(),
        ).to_dict()

    def select_files_dialog(self) -> dict[str, Any]:
        """ネイティブファイル選択ダイアログを開き、選択結果を返す。"""

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
        """ネイティブフォルダ選択ダイアログを開き、選択結果を返す。"""

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
        """画像ファイル登録サービスを取得し、未初期化の場合は初期化する。"""

        if self._import_service is None:
            self.initialize_app_backend()
        if self._import_service is None:
            raise RuntimeError("Image file import service is not initialized.")
        return self._import_service

    def _get_active_window(self) -> object | None:
        """現在利用可能なpywebviewウィンドウを返す。"""

        if not webview.windows:
            return None
        return webview.windows[0]
