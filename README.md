# AZViewer

AZViewer は、ローカル画像を登録・閲覧・検索・整理するための Windows 向けデスクトップアプリです。

Stable Diffusion WebUI で生成した画像のメタ情報、プロンプト由来タグ、生成元モデルを扱いやすくすることを主な目的にしています。画像をタイル表示しながら、タグやモデルで絞り込み、必要に応じて Stable Diffusion WebUI 用のワイルドカード `.txt` も出力できます。

![起動直後の画面](images/1.main.png)

## ダウンロード

最新版は GitHub Releases から取得できます。

- リリースページ: https://github.com/Sunao-Yoshii/AZViewer/releases/tag/1.2.0
- Windows 版: `AZViewer-windows-portable.zip`
- 対応 OS Win11 (Win 10 以前は多分無理…)

`AZViewer-windows-portable.zip` を展開し、`AZViewer.exe` を実行してください。Python 実行環境は同梱されているため、利用する PC に Python を別途インストールする必要はありません。

### 実行環境の要件

AZViewer は Windows 11 の最新パッチ適用済み環境での動作を前提にしています。

- OS: Windows 11 64bit
- .NET Framework: 4.8.1 以上
- WebView2 Runtime: Evergreen Runtime
- Python: インストール不要。CPython 3.12 由来の実行環境をアプリに同梱しています。
- Visual C++ Runtime: インストール不要。必要な `VCRUNTIME140.dll`、`VCRUNTIME140_1.dll`、`ucrtbase.dll` はアプリに同梱しています。

Windows 11 には通常 WebView2 Runtime が含まれますが、企業管理端末、オフライン環境、Windows コンポーネントの破損などで削除または無効化されている場合は、Microsoft Edge WebView2 Runtime の修復または再インストールが必要です。

### 展開と起動時の注意

- 既存の `AZViewer` フォルダへ上書き展開せず、古いフォルダを削除してから新しい `AZViewer-windows-portable.zip` を展開してください。`AZViewer.exe` と `_internal` のバージョンが混在すると起動に失敗することがあります。
- `C:\Program Files` などの管理者権限が必要な場所ではなく、ユーザーが書き込めるフォルダへ展開してください。AZViewer は起動場所配下の `data` フォルダにデータベースとサムネイルキャッシュを作成します。
- セキュリティソフトや Microsoft Defender により `_internal` 配下の DLL が隔離された場合、起動に失敗することがあります。隔離履歴を確認し、ZIP を再展開してください。
- ダブルクリック起動で何も表示されず終了する場合は、`%LOCALAPPDATA%\AZViewer\logs\azviewer.log` を確認してください。起動時の例外や runtime 初期化エラーを記録します。`%LOCALAPPDATA%` に書き込めない環境では、展開先の `logs\azviewer.log`、カレントディレクトリの `logs\azviewer.log`、一時フォルダの `AZViewer\logs\azviewer.log` の順に出力先を切り替えます。
- ログ出力先を明示したい場合は、環境変数 `AZVIEWER_LOG_DIR` にログフォルダのパスを設定してください。

## 主な機能

- ローカル画像の登録、閲覧、詳細表示
- ファイル選択、フォルダ選択、ドラッグ&ドロップによる画像登録
- `png`, `jpg`, `jpeg`, `webp`, `avif` 形式への対応
- レーティング、チェック状態、お気に入り、コメントの編集
- 画像ごとのタグ管理
- Stable Diffusion WebUI の Positive prompt を読み取り、タグとして一括登録
- 生成元モデル名の登録、表示、検索
- パス、レーティング、チェック状態、お気に入り、タグ、フォルダ、モデルによる検索
- 同じタグ構成を持つ画像の検索
- 選択画像の一括ファイル移動
- 選択画像の一括物理削除
- 選択画像のタグを Stable Diffusion WebUI ワイルドカード `.txt` として出力
- 画像メタ情報の表示、コピー、タグ入力への流用

![画像登録後のサンプル画面](images/4.sample.png)

## 基本的な使い方

### 1. 画像を登録する

左側の登録エリアから画像ファイルまたはフォルダを選択します。画像やフォルダをアプリ画面へドラッグ&ドロップして登録することもできます。

フォルダ登録では、対象フォルダ直下の対応画像ファイルを登録します。登録済み画像はタイル形式で一覧表示されます。

### 2. 画像を探す

検索フォームから、パス、レーティング、チェック状態、お気に入り、タグ、フォルダ、生成元モデルで絞り込めます。

タグ検索は最大 3 件まで指定でき、複数指定時は AND 条件で検索します。フォルダ検索とモデル検索は、候補一覧から 1 件を選ぶ完全一致検索です。

### 3. 画像情報を編集する

各画像タイルから、レーティング、チェック状態、お気に入り、コメント、タグ、生成元モデルを編集できます。

タグはカンマ区切りで複数入力できます。Stable Diffusion WebUI のプロンプトからタグを作る場合は、メタ情報表示から必要な範囲を選択し、タグ入力欄へ流用できます。

### 4. プロンプトを一括で読み取る

ヘッダーの「プロンプトの読み取り」から、タグ未登録の画像を対象に Stable Diffusion WebUI の Positive prompt を読み取り、タグとして登録できます。

既にタグが登録されている画像は対象外です。生成元モデルが未設定の画像については、メタ情報からモデル名を読み取れる場合にモデル情報も登録します。

### 5. 画像を整理する

画像一覧で複数画像を選択すると、一括操作を実行できます。

- ファイルを移動: 選択画像の実ファイルを指定フォルダへ移動し、AZViewer 上のパス情報も更新します。
- 選択画像を削除: AZViewer 上の登録情報、サムネイルキャッシュ、実際の画像ファイルをまとめて削除します。
- ワイルドカード出力: 選択画像のタグを `1画像 = 1行` の `.txt` として保存、または既存ファイルへ追記します。

## データ保存について

AZViewer はローカルの SQLite データベースで登録情報を管理します。標準では、起動した場所の `data/az_data.sqlite3` に保存されます。サムネイルキャッシュも `data` 配下に作成されます。

登録される主な情報は、画像ファイルのパス、レーティング、チェック状態、お気に入り、コメント、タグ、生成元モデルです。元画像そのものをアプリ内にコピーするのではなく、ローカルファイルの場所を参照して管理します。

## 注意事項

- 一括物理削除は、AZViewer 上の登録情報だけでなく実際の画像ファイルも削除します。実行前に対象画像を確認してください。
- 一括移動や一括削除では、ファイル操作と DB 更新を組み合わせて処理します。重要な画像を扱う場合は事前にバックアップを取ってください。
- 画像メタ情報はファイル形式や生成環境によって異なります。すべての画像でプロンプトやモデル名を取得できるとは限りません。
- ワイルドカード出力は、AZViewer に登録済みのタグを元に生成します。保存前にプレビューを確認してください。
- 開発版で作成した古い DB を使い回す場合、正式版の DB 構造と合わない可能性があります。必要に応じて `data` 配下をバックアップしてください。

## 開発者向け

このアプリは pywebview + Vue + Bootstrap で構成されています。

### ローカル実行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

cd frontend
npm install
npm run build
cd ..

python backend\main.py
```

### フロントエンド開発サーバー

```powershell
cd frontend
npm run dev
```

別の PowerShell で pywebview を起動します。

```powershell
$env:AZVIEWER_FRONTEND_URL = "http://127.0.0.1:5173"
python backend\main.py
```

### Windows リリースビルド

リリースビルドは `C:\Python312\python.exe` にインストールした 64bit CPython 3.12 を使用します。PATH に Python を追加する必要はありません。

```powershell
.\build_windows.ps1
```

ビルドが成功すると、以下が生成されます。

- `dist\AZViewer\AZViewer.exe`
- `dist\AZViewer-windows-portable.zip`

ビルド時には、配布物に Python runtime、pythonnet、clr-loader、WebView2 の .NET interop DLL、Visual C++ runtime が同梱されていることを検証し、完成した EXE で `pythonnet` / WinForms バックエンドの smoke test を実行します。

---

リリースビルドの各種ライブラリバージョンを固定化しました。

- pywebview==6.2.1
- pythonnet==3.0.5
- clr-loader==0.2.10
- Pillow>=11.0.0 はそのまま維持
- pyinstaller==6.20.0
