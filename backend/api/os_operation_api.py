from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from .api_response import ApiResponse


# 環境、OS依存のコマンド類を実行する
class OsOperationApi:
    """OS依存の操作を提供する。"""

    def open_containing_folder(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """指定ファイルが存在するフォルダをエクスプローラで開く。"""

        data = payload if isinstance(payload, dict) else {}
        path = Path(str(data.get("path") or "")).expanduser()
        if not path.is_file():
            return ApiResponse(success=False, message="File was not found.", data=None).to_dict()

        if sys.platform != "win32":
            return ApiResponse(success=False, message="Explorer is only available on Windows.", data=None).to_dict()

        try:
            subprocess.Popen(["explorer.exe", str(path.parent)])
        except OSError as exc:
            return ApiResponse(success=False, message=str(exc), data=None).to_dict()

        return ApiResponse(success=True, message="Folder opened.", data={"path": str(path.parent)}).to_dict()
