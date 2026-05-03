from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image


class ImageMetadataService:
    """画像ファイルのメタ情報を表示用テキストとして取得する。"""

    def fetch_metadata_text(self, path: str) -> str:
        image_path = Path(path)
        if not image_path.exists():
            raise FileNotFoundError(f"画像ファイルが存在しません: {path}")
        if not image_path.is_file():
            raise ValueError(f"画像ファイルではありません: {path}")

        with Image.open(image_path) as image:
            return self._build_metadata_text(image_path, image)

    def _build_metadata_text(self, image_path: Path, image: Image.Image) -> str:
        lines = [
            f"filename: {image_path.name}",
            f"path: {image_path}",
            f"format: {image.format or ''}",
            f"mode: {image.mode}",
            f"width: {image.width}",
            f"height: {image.height}",
        ]

        for key, value in dict(image.info or {}).items():
            lines.extend(self._format_metadata_value(str(key), value))

        return "\n".join(lines)

    def _format_metadata_value(self, key: str, value: Any) -> list[str]:
        text = self._to_text(value)
        if "\n" in text:
            return [
                f"{key}: |",
                *[f"  {line}" for line in text.splitlines()],
            ]

        return [f"{key}: {text}"]

    def _to_text(self, value: Any) -> str:
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8", errors="replace")
            except Exception:
                return repr(value)

        return str(value)
