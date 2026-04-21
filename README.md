# AZViewer

pywebview + Vue + Bootstrap application foundation.

## Structure

```text
backend/
  main.py
  api/app_api.py
frontend/
  src/
    components/layout/
    pages/
    services/
```

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
