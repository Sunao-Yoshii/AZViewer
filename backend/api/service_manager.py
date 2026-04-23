from __future__ import annotations

from typing import Callable

from backend.db import ConnectionManager
from backend.repositories import ImageFileRepository
from backend.services import (
    DialogService,
    FileScanService,
    ImageFileImportService,
    StartupCleanupService,
)


class ServiceManager:
    """ConnectionManager と各種サービスの生成・保持を担当する。"""

    def __init__(self, window_provider: Callable[[], object | None]) -> None:
        """必要な接続管理とサービス参照を未初期化状態で準備する。"""

        self._connection_manager = ConnectionManager()
        self._dialog_service = DialogService(window_provider)
        self._repository: ImageFileRepository | None = None
        self._import_service: ImageFileImportService | None = None
        self._cleanup_service: StartupCleanupService | None = None
        self._initialized = False

    def initialize(self) -> None:
        """データベース接続と各種サービスを初期化する。"""

        if self._initialized:
            return

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
        self._initialized = True

    def close(self) -> None:
        """保持している接続を閉じる。"""

        self._connection_manager.close()

    @property
    def import_service(self) -> ImageFileImportService:
        """画像登録サービスを返す。"""

        self.initialize()
        if self._import_service is None:
            raise RuntimeError("Image file import service is not initialized.")
        return self._import_service

    @property
    def cleanup_service(self) -> StartupCleanupService:
        """起動時整合性確認サービスを返す。"""

        self.initialize()
        if self._cleanup_service is None:
            raise RuntimeError("Startup cleanup service is not initialized.")
        return self._cleanup_service

    @property
    def dialog_service(self) -> DialogService:
        """ファイル選択ダイアログサービスを返す。"""

        return self._dialog_service
