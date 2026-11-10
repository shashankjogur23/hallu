# HalluGuard — AI Hallucination Detection & Verification System

HalluGuard is a hybrid, production-grade hallucination detection system designed to detect, highlight, and categorize factual inconsistencies and unsupported claims in AI-generated responses against reference source text.

---

## 🌟 Key Features

- **Hybrid Detection Pipeline**:
  - **Primary Token Classifier**: [LettuceDetect ModernBERT](https://huggingface.co/KRLabsOrg/lettucedect-base-modernbert-en-v1) (`KRLabsOrg/lettucedect-base-modernbert-en-v1`) for token-level suspicious span detection.
  - **Secondary Cross-Encoder**: [DeBERTa-v3 NLI](https://huggingface.co/cross-encoder/nli-deberta-v3-small) (`cross-encoder/nli-deberta-v3-small`) for relational, compound, and ordinal contradiction verification.
- **Transparent 4-Way Verdict System**:
  - `SUPPORTED`: All statements are grounded in and substantiated by reference context.
  - `CONTRADICTED`: Claims directly conflict with statements in reference evidence.
  - `UNSUPPORTED`: Claims contain information not established by the reference evidence.
  - `INSUFFICIENT_EVIDENCE`: Provided reference context is missing or inadequate.
- **Proposition Decomposition**:
  - Clause-level proposition splitting for compound sentences with participial phrase and Oxford-comma protection.
- **Interactive Web Interface**:
  - React 19 + TypeScript + Vite + TailwindCSS frontend with color-coded span highlighting, metrics breakdown, and real-time verification.
- **Document Management & Persistence**:
  - PDF & TXT document ingestion, chunking, and TF-IDF context retrieval.
  - Optional PostgreSQL/Supabase integration for permanent storage and historical audit logging.

---

## 🏗️ Architecture

```
User Input (Answer + Reference Passages)
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
LettuceDetect ModernBERT    DeBERTa-v3 NLI
 (Token Span Classifier)   (Proposition NLI)
         │                       │
         └───────────┬───────────┘
                     ▼
           Transparent Decision
              Fusion Engine
                     │
                     ▼
     4-Way Verdict + Highlightable Spans
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ and `pnpm` (or `npm`)
- CPU or CUDA-capable machine

### 1. Backend Setup

```bash
cd backend

# Create & activate virtual environment (optional if using global)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be live at:
- **API URL**: `http://localhost:8000/`
- **Interactive Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Start Vite dev server
pnpm run dev
```

The UI will be accessible at **`http://localhost:5173/`**.

---

## ⚙️ Configuration (`.env`)

Copy `backend/.env.example` to `backend/.env` to configure optional settings:

```ini
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000

# Models
MODEL_PATH=KRLabsOrg/lettucedect-base-modernbert-en-v1
NLI_ENABLED=true
NLI_MODEL_PATH=cross-encoder/nli-deberta-v3-small
NLI_CONTRADICTION_THRESHOLD=0.65

# Supabase (Optional)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key-here
```

---

## 🧪 Testing

```bash
cd backend

# Run full pytest suite (27 tests)
pytest tests/ -v

# Run verification test suite
python run_tests.py
```


