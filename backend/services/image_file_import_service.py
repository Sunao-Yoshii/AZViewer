from __future__ import annotations

from sqlite3 import Connection
from typing import Any

from backend.models import ImportResult
from backend.repositories import ImageFileRepository
from backend.services.file_scan_service import FileScanService


class ImageFileImportService:
    def __init__(
        self,
        connection: Connection,
        repository: ImageFileRepository,
        file_scan_service: FileScanService,
    ) -> None:
        self._connection = connection
        self._repository = repository
        self._file_scan_service = file_scan_service

    def import_items(self, payload: dict[str, Any]) -> ImportResult:
        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return ImportResult(
                success=False,
                error_summary="入力データが不正です。",
                failed_files=[],
                message="payload.items must be a list.",
            )

        try:
            paths = self._file_scan_service.collect_image_paths(items)
        except Exception as exc:
            return ImportResult(
                success=False,
                error_summary="ファイルの解析中にエラーが発生しました。",
                failed_files=[
                    str(item.get("path"))
                    for item in items
                    if isinstance(item, dict) and item.get("path")
                ],
                message=str(exc),
            )

        existing_paths = set(self._repository.find_all_paths())
        target_paths = [path for path in paths if str(path) not in existing_paths]
        records = [self._file_scan_service.build_record(path) for path in target_paths]

        if not records:
            return ImportResult(
                success=True,
                imported_count=0,
                skipped_count=len(paths),
            )

        try:
            self._connection.execute("BEGIN")
            self._repository.insert_many(records)
            self._connection.commit()
        except Exception as exc:
            self._connection.rollback()
            return ImportResult(
                success=False,
                error_summary="データ登録中にエラーが発生しました。",
                failed_files=[record.path for record in records],
                message=str(exc),
            )

        return ImportResult(
            success=True,
            imported_count=len(records),
            skipped_count=len(paths) - len(records),
        )
