from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import ExifTags, Image

EXIF_READABLE_EXTENSIONS = {".jpg", ".jpeg", ".webp", ".avif"}
EXIF_USER_COMMENT_PREFIXES = {
    b"ASCII\x00\x00\x00": "ascii",
    b"UNICODE\x00": "utf-16-be",
    b"JIS\x00\x00\x00\x00\x00": "shift_jis",
}
EXIF_UTF16LE_TAGS = {
    "XPTitle",
    "XPComment",
    "XPAuthor",
    "XPKeywords",
    "XPSubject",
}
EXIF_POINTER_TAGS = {
    "ExifOffset",
    "GPSInfo",
    "InteroperabilityOffset",
}
EXIF_IFD_SPECS = [
    (ExifTags.IFD.Exif, "exif", ExifTags.TAGS),
    (ExifTags.IFD.GPSInfo, "gps", ExifTags.GPSTAGS),
    (ExifTags.IFD.Interop, "interop", ExifTags.TAGS),
    (ExifTags.IFD.IFD1, "thumbnail", ExifTags.TAGS),
]
PROMPT_METADATA_KEYS_BY_EXTENSION = {
    ".png": "parameters",
    ".jpg": "exif.UserComment",
    ".jpeg": "exif.UserComment",
    ".webp": "exif.UserComment",
    ".avif": "exif.UserComment",
}


class ImageMetadataService:
    """画像ファイルのメタ情報を表示用テキストとして取得する。"""

    def fetch_metadata_text(self, path: str) -> str:
        image_path = Path(path)
        if not image_path.exists():
            raise FileNotFoundError(f"画像ファイルが存在しません: {path}")
        if not image_path.is_file():
            raise ValueError(f"画像ファイルではありません: {path}")

        with Image.open(image_path) as image:
            return "\n".join(self._build_metadata_list(image_path, image))

    def extract_stable_diffusion_prompt(self, path: str) -> str | None:
        """Stable Diffusion WebUIのPositive prompt部分を画像メタ情報から抽出する。"""

        image_path = Path(path)
        if not image_path.exists():
            raise FileNotFoundError(f"画像ファイルが存在しません: {path}")
        if not image_path.is_file():
            raise ValueError(f"画像ファイルではありません: {path}")

        target_key = PROMPT_METADATA_KEYS_BY_EXTENSION.get(image_path.suffix.lower())
        if target_key is None:
            return None

        with Image.open(image_path) as image:
            lines = self._build_metadata_list(image_path, image)

        value = self._extract_metadata_value(lines, target_key)
        if value is None:
            return None

        prompt = self._extract_positive_prompt(value).strip()
        return prompt or None

    def _build_metadata_list(self, image_path: Path, image: Image.Image) -> list:
        lines = [
            f"filename: {image_path.name}",
            f"path: {image_path}",
            f"format: {image.format or ''}",
            f"mode: {image.mode}",
            f"width: {image.width}",
            f"height: {image.height}",
        ]

        for key, value in self._get_image_info_items(image):
            lines.extend(self._format_metadata_value(key, value))

        if self._should_read_exif_as_text(image_path):
            lines.extend(self._format_exif_metadata(image))

        return lines

    def _get_image_info_items(self, image: Image.Image) -> list[tuple[str, Any]]:
        """Pillowのinfoから表示向けメタ情報を取得する。"""

        return [
            (str(key), value)
            for key, value in dict(image.info or {}).items()
            if str(key).lower() != "exif"
        ]

    def _should_read_exif_as_text(self, image_path: Path) -> bool:
        """EXIF文字列をタグ単位でUnicode化する対象画像か判定する。"""

        return image_path.suffix.lower() in EXIF_READABLE_EXTENSIONS

    def _format_exif_metadata(self, image: Image.Image) -> list[str]:
        """EXIFタグをUnicode文字列データとして表示用に整形する。"""

        try:
            exif = image.getexif()
        except Exception:
            return []

        lines: list[str] = []
        for tag_id, value in exif.items():
            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
            if tag_name in EXIF_POINTER_TAGS:
                continue
            lines.extend(self._format_metadata_value(f"exif.{tag_name}", value))
        lines.extend(self._format_nested_exif_metadata(exif))
        return lines

    def _format_nested_exif_metadata(self, exif: Image.Exif) -> list[str]:
        """ExifOffsetなどが指す子IFDのEXIF値を展開する。"""

        lines: list[str] = []
        for ifd_id, prefix, tag_names in EXIF_IFD_SPECS:
            lines.extend(self._format_exif_ifd(exif, ifd_id, prefix, tag_names))
        return lines

    def _format_exif_ifd(
        self,
        exif: Image.Exif,
        ifd_id: ExifTags.IFD,
        prefix: str,
        tag_names: dict[int, str],
    ) -> list[str]:
        """指定IFDに含まれるEXIFタグを表示用に整形する。"""

        try:
            ifd = exif.get_ifd(ifd_id)
        except Exception:
            return []

        lines: list[str] = []
        for tag_id, value in ifd.items():
            tag_name = tag_names.get(tag_id, str(tag_id))
            lines.extend(self._format_metadata_value(f"{prefix}.{tag_name}", value))
        return lines

    def _format_metadata_value(self, key: str, value: Any) -> list[str]:
        text = self._to_text(value, key=key)
        if "\n" in text:
            return [
                f"{key}: |",
                *[f"  {line}" for line in text.splitlines()],
            ]

        return [f"{key}: {text}"]

    def _extract_metadata_value(self, lines: list[str], target_key: str) -> str | None:
        """YAML風表示行から指定キーの値を復元する。"""

        prefix = f"{target_key}:"
        for index, line in enumerate(lines):
            if not line.startswith(prefix):
                continue

            value = line[len(prefix):].lstrip()
            if value == "|":
                return self._extract_metadata_block(lines[index + 1:])
            return value

        return None

    def _extract_metadata_block(self, lines: list[str]) -> str:
        """YAML風ブロック形式のインデント本文を連結する。"""

        block_lines: list[str] = []
        for line in lines:
            if not line.startswith("  "):
                break
            block_lines.append(line[2:])
        return "\n".join(block_lines)

    def _extract_positive_prompt(self, value: str) -> str:
        """WebUIメタ情報本文からPositive promptだけを切り出す。"""

        negative_index = value.find("Negative prompt:")
        if negative_index >= 0:
            return value[:negative_index]

        steps_index = value.find("Steps:")
        if steps_index >= 0:
            return value[:steps_index]

        return value

    def _to_text(self, value: Any, *, key: str = "") -> str:
        if isinstance(value, bytes):
            return self._decode_bytes(value, key=key)

        if isinstance(value, tuple):
            return ", ".join(self._to_text(item, key=key) for item in value)

        if isinstance(value, list):
            return ", ".join(self._to_text(item, key=key) for item in value)

        return str(value)

    def _decode_bytes(self, value: bytes, *, key: str) -> str:
        """EXIF由来のbytesを可能な範囲でUnicode文字列へ変換する。"""

        tag_name = key.rsplit(".", maxsplit=1)[-1]
        if tag_name in EXIF_UTF16LE_TAGS:
            try:
                return value.decode("utf-16le", errors="replace").rstrip("\x00")
            except Exception:
                pass

        user_comment = self._decode_user_comment(value)
        if user_comment is not None:
            return user_comment

        for encoding in self._candidate_encodings(value):
            try:
                return value.decode(encoding, errors="replace").rstrip("\x00")
            except Exception:
                continue

        return repr(value)

    def _decode_user_comment(self, value: bytes) -> str | None:
        """EXIF UserComment の文字コード接頭辞を解釈する。"""

        for prefix, encoding in EXIF_USER_COMMENT_PREFIXES.items():
            if value.startswith(prefix):
                return value[len(prefix):].decode(encoding, errors="replace").rstrip("\x00")
        return None

    def _candidate_encodings(self, value: bytes) -> list[str]:
        """EXIF bytesの推定デコード順を返す。"""

        if b"\x00" in value:
            return ["utf-16le", "utf-8"]
        return ["utf-8", "cp932", "latin-1"]
