# HalluGuard Backend 🛡️

HalluGuard is a hallucination detection framework for generative AI and Retrieval-Augmented Generation (RAG) applications.

This backend provides FastAPI REST endpoints powered by the official **KRLabsOrg/LettuceDetect** ModernBERT token-classification model (`KRLabsOrg/lettucedect-base-modernbert-en-v1`), providing exact character-level hallucination span detection and confidence scoring.

---

## Architecture Overview

```
HalluGuard/
└── backend/
    ├── app/
    │   ├── main.py                 # FastAPI application, lifespan model loading & CORS
    │   ├── config.py               # Pydantic environment settings
    │   ├── api/
    │   │   ├── health.py           # GET /health
    │   │   └── verification.py     # POST /verify, POST /context/chunk, POST /context/retrieve
    │   ├── services/
    │   │   ├── detector_service.py # LettuceDetect ModernBERT inference engine (CPU)
    │   │   ├── document_service.py # PyMuPDF PDF & TXT text extraction & chunking
    │   │   ├── retrieval_service.py# TF-IDF cosine similarity context retrieval
    │   │   └── supabase_service.py # PostgreSQL persistence & history via Supabase
    │   ├── schemas/
    │   │   └── verification.py     # Pydantic request & response models
    │   └── database/
    │       └── schema.sql          # Supabase PostgreSQL schema DDL
    ├── tests/
    │   ├── test_health.py          # GET /health tests
    │   ├── test_verification.py    # POST /verify tests (clean, hallucinated, edge cases)
    │   ├── test_document_service.py# PDF & TXT extraction & chunking tests
    │   ├── test_retrieval_service.py# TF-IDF context ranking tests
    │   └── test_supabase_service.py # Supabase missing credentials & degradation tests
    ├── requirements.txt            # Dependency specification
    ├── .env.example                # Environment variable template
    └── README.md                   # This documentation
```

---

## Key Features

1. **LettuceDetect Model Integration**:
   - Pretrained model: `KRLabsOrg/lettucedect-base-modernbert-en-v1`.
   - Loaded **once** at backend startup via FastAPI lifespan context manager.
   - Inference runs locally on CPU without external API charges or network calls once cached.
   - Preserves exact character offsets (`start`, `end`), extracted text substring, and probability confidence.

2. **REST Endpoints**:
   - `GET /health`: Returns service health, model loading status, device, and database readiness.
   - `POST /verify`: Performs hallucination verification over question, answer, and reference context.
   - `POST /context/chunk`: Splits raw document text into overlapping passages with offsets.
   - `POST /context/retrieve`: Ranks candidate passages against query using TF-IDF cosine similarity.
   - `GET /docs`: Built-in interactive Swagger UI.

3. **Document Processing**:
   - PDF text extraction using PyMuPDF (`pymupdf`).
   - TXT text extraction with multi-encoding fallback (UTF-8, Latin-1, CP1252).
   - Natural boundary chunking (paragraphs, sentences, word windows).

4. **Supabase Persistence**:
   - PostgreSQL schema for `documents`, `verifications`, and `verification_spans`.
   - Uses `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
   - Graceful local-only fallback if credentials are absent or incomplete (verification is never blocked).

---

## Setup & Running

### 1. Prerequisites
- Python 3.11
- Virtual environment with LettuceDetect installed (e.g. `F:\final project\LettuceDetect\.venv`)

### 2. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 3. Run the Backend Server
From `F:\final project\HalluGuard\backend`:
```powershell
# Using the existing LettuceDetect Python virtual environment
Set-Location "F:\final project\HalluGuard\backend"
& "F:\final project\LettuceDetect\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Interactive API Documentation
Open your browser to:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Database Setup (Supabase)

To enable database persistence for verification history and document tracking:

1. Create a project at [supabase.com](https://supabase.com).
2. Open the **SQL Editor** in the Supabase Dashboard.
3. Paste and run the contents of [`app/database/schema.sql`](app/database/schema.sql).
4. Navigate to **Project Settings -> API** and copy:
   - Project URL -> `SUPABASE_URL`
   - `service_role` secret key -> `SUPABASE_SERVICE_ROLE_KEY`
5. Add these to your `.env` file.

