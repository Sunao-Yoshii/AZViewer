from __future__ import annotations

import logging
from typing import Any

from backend.repositories import ImageFileRepository
from backend.services import StartupCleanupService

from .api_response import ApiResponse
from .default_template_api import DefaultTemplateApi
from .service_manager import ServiceManager

LOGGER = logging.getLogger(__name__)


class AppLifeCycleApi:
    """アプリケーションのライフサイクルイベントを処理する。"""

    def __init__(
        self,
        service_manager: ServiceManager,
        default_template_api: DefaultTemplateApi,
    ) -> None:
        """起動時に利用するサービス管理と基本APIを保持する。"""

        self._service_manager = service_manager
        self._default_template_api = default_template_api
        self._startup_cleanup_completed = False
        self._repository: ImageFileRepository | None = None
        self._cleanup_service: StartupCleanupService | None = None

    def initialize(self) -> dict[str, Any]:
        """互換用の初期化APIとしてアプリ初期化情報を返す。"""

        return self.bootstrap_app()

    def bootstrap_app(self) -> dict[str, Any]:
        """初回画面表示後の起動整合性確認を含むアプリ初期化結果を返す。"""

        try:
            self._service_manager.initialize()
        except Exception as exc:
            LOGGER.exception("Application initialization failed.")
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()

        startup_notification = None
        if not self._startup_cleanup_completed:
            try:
                startup_notification = self._run_startup_cleanup()
            finally:
                self._startup_cleanup_completed = True

        app_info = self._default_template_api.get_app_info()
        menu_definitions = self._default_template_api.get_menu_definitions()
        initialize_result = self._default_template_api.initialize_app()

        return ApiResponse(
            success=True,
            message="Application initialized.",
            data={
                "app": initialize_result.get("data"),
                "appInfo": app_info.get("data"),
                "menus": menu_definitions.get("data"),
                "startupNotification": startup_notification,
            },
        ).to_dict()

    def close(self) -> None:
        """アプリケーション終了時に保持している接続を閉じる。"""

        self._service_manager.close()

    def _run_startup_cleanup(self) -> dict[str, Any] | None:
        """起動時整合性確認を同期実行し、必要時のみ通知情報を返す。"""

        try:
            deleted_count = self._get_cleanup_service().cleanup_missing_files()
        except Exception:
            LOGGER.exception("Startup cleanup failed.")
            return {
                "type": "error",
                "message": "ファイル状態確認の実行中にエラーが発生しました",
            }

        if deleted_count < 1:
            return None

        return {
            "type": "info",
            "title": "ファイル状態確認が完了しました",
            "message": f"存在しないファイルの登録情報を {deleted_count} 件削除しました",
        }

    def _get_cleanup_service(self) -> StartupCleanupService:
        """起動時整合性確認サービスを取得し、未初期化の場合は初期化する。"""

        if self._cleanup_service is not None:
            return self._cleanup_service

        connection = self._service_manager.get_connection()
        self._repository = ImageFileRepository(connection)
        self._repository.create_table()
        self._cleanup_service = StartupCleanupService(connection, self._repository)
        return self._cleanup_service
