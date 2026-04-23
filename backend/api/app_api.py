from __future__ import annotations

import webview

from .app_lifecycle_api import AppLifeCycleApi
from .default_template_api import DefaultTemplateApi
from .image_catalog_api import ImageCatalogApi
from .image_register_api import ImageRegisterApi
from .service_manager import ServiceManager


class AppApi:
    """pywebviewを通じてVueへ公開するアプリケーションAPIを提供する。"""

    def __init__(self) -> None:
        """内部ロジックごとのAPIクラスを組み立てる。"""

        service_manager = ServiceManager()
        default_template_api = DefaultTemplateApi()
        image_catalog_api = ImageCatalogApi(service_manager)

        self._app_lifecycle_api = AppLifeCycleApi(
            service_manager,
            default_template_api,
            image_catalog_api,
        )
        self._default_template_api = default_template_api
        self._image_catalog_api = image_catalog_api
        self._image_register_api = ImageRegisterApi(service_manager, self._get_active_window)

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

    def update_image_file_flags(self, payload: dict[str, object]) -> dict[str, object]:
        """指定レコードのフラグを更新する。"""

        return self._image_catalog_api.update_image_file_flags(payload)

    def fetchLocalImageThumb(self, payload: dict[str, object]) -> dict[str, object]:
        """ローカル画像の表示用データURLを返す。"""

        return self._image_catalog_api.fetchLocalImageThumb(payload)

    def _get_active_window(self) -> object | None:
        """現在利用可能なpywebviewウィンドウを返す。"""

        if not webview.windows:
            return None
        return webview.windows[0]
