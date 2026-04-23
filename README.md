# AZViewer

pywebview + Vue + Bootstrap application foundation.

このリポジトリは、画像ファイルのビューワー兼、管理ツールを目指して実装されています。  
尚、このリポジトリは以下のルールで検証しながら実装しています。

1. バグフィックスなどを除き、原則的に AI 生成でのみソースコードを作成する
2. 人間の目で理解可能、保守可能な範囲を保つ
3. 一度にすべての仕様を指定せず、仕様の追加・変更を敢えて行いながら実装する

上記を通して、かき捨てではない保守可能なソースコードを維持する。

## Setup

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

## release build

```powershell
.\build_windows.ps1
```

## Development

Run the Vite dev server:

```powershell
cd frontend
npm run dev
```

Then start pywebview with the dev server URL:

```powershell
$env:AZVIEWER_FRONTEND_URL = "http://127.0.0.1:5173"
python backend\main.py
```
