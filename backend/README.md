Quarry.io Backend (FastAPI)

Prereqs
- Python 3.10+
- Tesseract OCR installed and on PATH (`tesseract --version`)

Install
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run
```bash
uvicorn app.main:app --reload --port 8000
```

API
- POST `/index` multipart files[]: indexes screenshots via OCR + embeddings (FAISS)
- GET `/search?q=text&k=12` search by text
- GET `/health`

Data
- Default data dir: `./data` (override via `QUARRY_DATA_DIR`)
- Stores `index.faiss`, `meta.jsonl`, and `images/{id}.jpg`


