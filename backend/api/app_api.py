from __future__ import annotations

import webview

from backend.services import ThumbnailCacheService

from .app_lifecycle_api import AppLifeCycleApi
from .database_lifecycle_manager import DatabaseLifecycleManager
from .default_template_api import DefaultTemplateApi
from .image_catalog_api import ImageCatalogApi
from .image_register_api import ImageRegisterApi
from .os_operation_api import OsOperationApi


class AppApi:
    """pywebviewを通じてVueへ公開するアプリケーションAPIを提供する。"""

    def __init__(self) -> None:
        """内部ロジックごとのAPIクラスを組み立てる。"""

        database_lifecycle_manager = DatabaseLifecycleManager()
        default_template_api = DefaultTemplateApi()
        os_operation_api = OsOperationApi()
        thumbnail_cache_service = ThumbnailCacheService()
        image_catalog_api = ImageCatalogApi(database_lifecycle_manager, thumbnail_cache_service)

        self._app_lifecycle_api = AppLifeCycleApi(
            database_lifecycle_manager,
            default_template_api,
            image_catalog_api,
            thumbnail_cache_service,
        )
        self._default_template_api = default_template_api
        self._image_catalog_api = image_catalog_api
        self._os_operation_api = os_operation_api
        self._image_register_api = ImageRegisterApi(
            database_lifecycle_manager,
            self._get_active_window,
            thumbnail_cache_service,
        )

    def close(self) -> None:
        """アプリケーション終了時に保持している接続を閉じる。"""

        self._app_lifecycle_api.close()

    def initialize(self) -> dict[str, object]:
        """互換用の初期化APIとしてアプリ初期化情報を返す。"""

        return self._app_lifecycle_api.initialize()

    def initialize_app(self) -> dict[str, object]:
        """Vue側の起動時に必要な初期化済みアプリ情報を返す。"""

        return self._default_template_api.initialize_app()

    def bootstrap_app(self) -> dict[str, object]:
        """初回画面表示後の起動整合性確認を含むアプリ初期化結果を返す。"""

        return self._app_lifecycle_api.bootstrap_app()

    def get_app_info(self) -> dict[str, object]:
        """アプリケーション名やバージョンなどの基本情報を返す。"""

        return self._default_template_api.get_app_info()

    def health_check(self) -> dict[str, object]:
        """Python APIが呼び出し可能か確認するための応答を返す。"""

        return self._default_template_api.health_check()

    def import_selected_items(self, payload: dict[str, object]) -> dict[str, object]:
        """選択またはドロップされたファイル情報を画像データとして登録する。"""

        return self._image_register_api.import_selected_items(payload)

    def select_files_dialog(self) -> dict[str, object]:
        """ネイティブファイル選択ダイアログを開き、選択結果を返す。"""

        return self._image_register_api.select_files_dialog()

    def select_folder_dialog(self) -> dict[str, object]:
        """ネイティブフォルダ選択ダイアログを開き、選択結果を返す。"""

        return self._image_register_api.select_folder_dialog()

    def search_image_files(self, payload: dict[str, object]) -> dict[str, object]:
        """画像一覧検索およびページング取得を行う。"""

        return self._image_catalog_api.search_image_files(payload)

    def update_image_file_detail(self, payload: dict[str, object]) -> dict[str, object]:
        """指定レコードの詳細項目を一括更新する。"""

        return self._image_catalog_api.update_image_file_detail(payload)

    def delete_image_file(self, payload: dict[str, object]) -> dict[str, object]:
        """指定レコードを削除する。"""

        return self._image_catalog_api.delete_image_file(payload)

    def fetchLocalImage(self, payload: dict[str, object]) -> dict[str, object]:
        """ローカル画像の本体を表示用データURLとして返す。"""

        return self._image_catalog_api.fetchLocalImage(payload)

    def fetchLocalImageThumb(self, payload: dict[str, object]) -> dict[str, object]:
        """ローカル画像の表示用データURL1を返す。"""

        return self._image_catalog_api.fetchLocalImageThumb(payload)

    def fetch_image_metadata(self, payload: dict[str, object]) -> dict[str, object]:
        """ローカル画像のメタ情報を表示用テキストとして返す。"""

        return self._image_catalog_api.fetch_image_metadata(payload)

    def fetch_tags_for_search(self, payload: dict[str, object]) -> dict[str, object]:
        """タグ検索候補を返す。"""

        return self._image_catalog_api.fetch_tags_for_search(payload)

    def fetch_folders_for_search(self, payload: dict[str, object]) -> dict[str, object]:
        """フォルダ検索候補を返す。"""

        return self._image_catalog_api.fetch_folders_for_search(payload)

    def import_prompt_tags(self, payload: dict[str, object] | None = None) -> dict[str, object]:
        """タグ未登録画像へプロンプト由来タグを一括登録する。"""

        return self._image_catalog_api.import_prompt_tags(payload)

    def open_containing_folder(self, payload: dict[str, object]) -> dict[str, object]:
        """指定ファイルが存在するフォルダをエクスプローラで開く。"""

        return self._os_operation_api.open_containing_folder(payload)

    def _get_active_window(self) -> object | None:
        """現在利用可能なpywebviewウィンドウを返す。"""

        if not webview.windows:
            return None
        return webview.windows[0]
