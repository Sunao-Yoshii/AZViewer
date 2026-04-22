from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.models import ImageFileRecord


class FileScanService:
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".avif"}

    def is_supported_image(self, path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def collect_image_paths(self, items: list[dict[str, Any]]) -> list[Path]:
        collected: list[Path] = []

        for item in items:
            raw_path = str(item.get("path") or "").strip()
            if not raw_path:
                continue

            item_type = str(item.get("type") or "").lower()
            path = Path(raw_path).expanduser().resolve()

            if item_type == "directory" or path.is_dir():
                collected.extend(self._collect_direct_children(path))
                continue

            if self.is_supported_image(path):
                collected.append(path)

        return self._dedupe_paths(collected)

    def build_record(self, path: Path) -> ImageFileRecord:
        return ImageFileRecord(
            filename=path.name,
            path=str(path),
            folder=path.parent.name,
        )

    def _collect_direct_children(self, directory: Path) -> list[Path]:
        if not directory.is_dir():
            return []

        return [
            child.resolve()
            for child in directory.iterdir()
            if self.is_supported_image(child)
        ]

    def _dedupe_paths(self, paths: list[Path]) -> list[Path]:
        seen: set[str] = set()
        deduped: list[Path] = []

        for path in paths:
            key = str(path)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(path)

        return deduped
