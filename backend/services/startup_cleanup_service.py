from __future__ import annotations

from pathlib import Path
from sqlite3 import Connection

from backend.repositories import ImageFileRepository


class StartupCleanupService:
    def __init__(self, connection: Connection, repository: ImageFileRepository) -> None:
        self._connection = connection
        self._repository = repository

    def cleanup_missing_files(self) -> None:
        paths = self._repository.find_all_paths()
        missing_paths = [path for path in paths if not Path(path).is_file()]

        if not missing_paths:
            return

        self._repository.delete_by_paths(missing_paths)
        self._connection.commit()
