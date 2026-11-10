# HalluGuard — Phase 5, Step 1: Deployment Readiness Inspection Report

**Date:** 2026-11-10  
**Phase:** Phase 5 — Deployment (Step 1: Deployment Readiness Inspection)  
**Status:** Inspection Completed — Project is Structurally Sound and Deployment-Ready with Minor Configuration Requirements  
**Project Root:** `F:\final project\HalluGuard`  
**LettuceDetect Root:** `F:\final project\LettuceDetect`  
**Model Identifier:** `KRLabsOrg/lettucedect-base-modernbert-en-v1`

---

## 1. Executive Summary

A comprehensive deployment readiness inspection was conducted across the **HalluGuard** codebase, covering the FastAPI backend, the React/Vite/TypeScript frontend, the pretrained LettuceDetect ModernBERT model integration, and cloud hosting infrastructure considerations.

### Overall Readiness Determination: **READY WITH MINOR CONFIGURATION**
- **Core Verification Engine:** Fully operational on CPU with verified 90.0% answer-level accuracy and 100% precision (0% false positive rate) on the geography benchmark.
- **Backend Architecture:** Modular, clean, thread-safe, and capable of operating autonomously with or without external database credentials.
- **Frontend Build:** Builds cleanly in 2.58 seconds with zero TypeScript or bundling errors, generating an optimized static asset bundle (`dist/`).
- **Google Cloud Deployment Path:** A single Compute Engine virtual machine (`e2-standard-2`) with Nginx reverse proxying is determined to be the simplest, most cost-effective, and most reliable deployment architecture.
- **Critical Blockers:** **Zero hard blockers.** Three minor configuration prerequisites were identified and documented for resolution during Step 2.

---

## 2. Readiness Scorecard

| Area | Component | Status | Detailed Finding |
| :--- | :--- | :---: | :--- |
| **Backend** | Application Entry Point (`app/main.py`) | `READY` | Standard FastAPI application with lifespan context manager. |
| **Backend** | Model Lifecycle Management | `READY` | Model loads once at startup into memory; persists for process duration. |
| **Backend** | CPU Inference Configuration | `READY` | Configured for `device="cpu"`; no GPU dependencies required. |
| **Backend** | API Endpoints & Routing | `READY` | All 10 REST endpoints implemented, typed, and schema-validated. |
| **Backend** | CORS Configuration | `READY` | Middleware configured to allow necessary origins, methods, and headers. |
| **Backend** | Database Graceful Degradation | `READY` | Operates in-memory if Supabase credentials are not provided. |
| **Backend** | Dependencies Specification | `NEEDS CONFIGURATION` | `python-multipart` missing from `requirements.txt`; `LettuceDetect` submodule path needs automated installation step. |
| **Frontend** | Build System & Asset Compilation | `READY` | Vite 8 + React 19 + Tailwind v4 compiles to `dist/` with 0 errors in 2.58s. |
| **Frontend** | Application Routing | `READY` | State-based navigation eliminates SPA 404 server-side rewrite issues. |
| **Frontend** | API Base URL Configuration | `NEEDS CONFIGURATION` | Defaults to `http://localhost:8000`; needs public server IP / domain or relative reverse-proxy configuration. |
| **Model** | Hardware Sizing & RAM Budget | `READY` | Model weights = 598.4 MB; runtime memory footprint = ~1.5 GB RAM. |
| **Model** | Model File Caching | `READY` | Cached locally in HuggingFace hub; downloads automatically on first run. |
| **Cloud** | Target Cloud Architecture | `READY` | Google Cloud Compute Engine (`e2-standard-2`) recommended over Cloud Run. |
| **Cloud** | SSL / HTTPS & Public Access | `NEEDS CONFIGURATION` | Requires domain mapping and Certbot / Let's Encrypt automated setup. |

---

## 3. Backend Inspection (Task 1)

### 3.1 Application Entry Point & Lifespan
- **File:** [`backend/app/main.py`](file:///f:/final%20project/HalluGuard/backend/app/main.py#L27-L65)
- **Lifespan Manager:** Uses FastAPI's `@asynccontextmanager lifespan(app: FastAPI)` pattern.
- **Model Loading:** Calls `detector_service.load_model()` once on application boot. If loading encounters an exception, the application does not crash; `/health` reports degraded status while `detector_service.is_loaded` remains `False`.
- **Inference Singleton:** A global `detector_service` singleton (`app.services.detector_service.detector_service`) holds the loaded model across all incoming web requests.
- **Production Startup Command:**
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
  ```
  *(Note: Single worker is recommended for CPU inference to avoid duplicating the 1.5 GB model in RAM across multiple worker processes).*

### 3.2 Python Runtime & Dependencies
- **Runtime Version:** Python 3.11.x (verified in `.venv`).
- **Inspected Requirements:** [`backend/requirements.txt`](file:///f:/final%20project/HalluGuard/backend/requirements.txt)
  - Core: `fastapi>=0.115.0`, `uvicorn[standard]>=0.30.0`, `pydantic>=2.9.0`, `python-dotenv>=1.0.1`
  - ML Engine: `torch>=2.4.0`, `transformers>=4.48.0`, `scikit-learn>=1.5.0`, `numpy>=2.0.0`
  - Document Engine: `pymupdf>=1.24.0`
  - Database: `supabase>=2.8.0`
- **Identified Deficiency (`NEEDS CONFIGURATION`):**
  1. `python-multipart` is required for FastAPI `UploadFile` processing on `/documents/upload`. It is installed in the local `.venv` but absent from `requirements.txt`.
  2. `lettucedetect` is currently installed in editable mode (`pip install -e ../LettuceDetect`). For production containerization or VM setup, the `LettuceDetect` repository must be cloned or installed during deployment.

### 3.3 Complete Endpoint Manifest
The backend exposes 10 primary REST routes plus OpenAPI documentation:

| HTTP Method | Route | Router Module | Purpose | Status |
| :--- | :--- | :--- | :--- | :---: |
| `GET` | `/` | `app.main` | Service root and documentation redirect | `READY` |
| `GET` | `/health` | `app.api.health` | System health, model readiness, device, DB status | `READY` |
| `POST` | `/verify` | `app.api.verification` | Core ModernBERT hallucination verification & span scoring | `READY` |
| `POST` | `/context/chunk` | `app.api.verification` | Splits raw text into sentence-bounded overlapping chunks | `READY` |
| `POST` | `/context/retrieve` | `app.api.verification` | TF-IDF passage retrieval and relevance ranking | `READY` |
| `GET` | `/verifications/history` | `app.api.verification` | Recent verification activity logs | `READY` |
| `GET` | `/verifications/stats` | `app.api.verification` | Summary metrics (total, clean, flagged, mean confidence) | `READY` |
| `POST` | `/documents/upload` | `app.api.documents` | Multipart upload for PDF and TXT reference documents | `READY` |
| `GET` | `/documents` | `app.api.documents` | List registered documents with metadata | `READY` |
| `GET` | `/documents/{id}` | `app.api.documents` | Retrieve specific document with extracted text and chunks | `READY` |
| `DELETE` | `/documents/{id}` | `app.api.documents` | Remove document from registry | `READY` |
| `GET` | `/docs`, `/redoc` | FastAPI Builtin | Interactive Swagger UI and ReDoc documentation | `READY` |

### 3.4 CORS & Security Headers
- **Configuration:** [`backend/app/main.py`](file:///f:/final%20project/HalluGuard/backend/app/main.py#L67-L73)
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- **Readiness:** Permissive for testing. For strict production security behind a custom domain, `allow_origins` can optionally be scoped to the production domain.

### 3.5 File Uploads & Storage Architecture
- **Supported Formats:** PDF (`.pdf`) and Plain Text (`.txt`).
- **Processing:** In-memory extraction via PyMuPDF (`pymupdf.open(stream=bytes)`) without saving unencrypted temporary files to disk.
- **Storage Tier:**
  - *Tier 1 (In-Memory):* Session dictionary `document_service._documents`. Fast and self-contained; resets on server restart.
  - *Tier 2 (Supabase PostgreSQL):* Configured in [`backend/app/database/schema.sql`](file:///f:/final%20project/HalluGuard/backend/app/database/schema.sql). When credentials are provided, saves metadata to `documents`, `verifications`, and `verification_spans` tables.
- **Graceful Fallback:** If `SUPABASE_URL` is empty or untouched, the backend runs in local in-memory mode without errors.

---

## 4. Frontend Inspection (Task 2)

### 4.1 Framework & Core Dependencies
- **Inspected File:** [`frontend/package.json`](file:///f:/final%20project/HalluGuard/frontend/package.json)
- **Core Frameworks:**
  - `react`: `^19.3.1`
  - `react-dom`: `^19.3.1`
  - `vite`: `^8.3.6`
  - `tailwindcss`: `^4.3.5` (via `@tailwindcss/vite`)
  - `lucide-react`: `^1.71.0`
  - `typescript`: `~7.0.2`

### 4.2 Build Verification & Output
- **Build Command:** `npm run build` (`tsc -b && vite build`)
- **Execution Test:** Executed cleanly during inspection in **2.58 seconds** with 0 errors.
- **Output Directory:** `frontend/dist/`
  - `dist/index.html` (0.51 kB)
  - `dist/assets/index-CGr_GgUF.css` (38.94 kB, gzip: 7.49 kB)
  - `dist/assets/index-BvH5GY--.js` (292.88 kB, gzip: 85.33 kB)
- **Asset Weight:** Total bundle size is under 350 kB, enabling near-instantaneous browser load times.

### 4.3 API Client & Base URL Configuration
- **Inspected File:** [`frontend/src/services/api.ts`](file:///f:/final%20project/HalluGuard/frontend/src/services/api.ts#L17)
  ```typescript
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  ```
- **Deployment Requirement (`NEEDS CONFIGURATION`):**
  - In `frontend/.env`, `VITE_API_BASE_URL` is set to `http://localhost:8000`.
  - When deployed, client browsers running outside the server machine cannot reach `localhost:8000`.
  - **Resolution Options:**
    1. *Relative Path via Nginx (Recommended):* Set `VITE_API_BASE_URL=""` and let Nginx proxy `/verify`, `/health`, `/documents` directly to backend port 8000 on the same host.
    2. *Absolute URL:* Set `VITE_API_BASE_URL=https://api.yourdomain.com` or `http://<SERVER_IP>:8000` at build time.

### 4.4 Routing Architecture
- **Implementation:** [`frontend/src/App.tsx`](file:///f:/final%20project/HalluGuard/frontend/src/App.tsx#L10-L56)
- **Finding:** Navigation is handled entirely through React internal state (`currentPage` state hook) rather than HTML5 browser history (`react-router-dom`).
- **Benefit:** Static web servers (Nginx, Apache, Cloud Storage) will never encounter 404 routing errors on page refresh, because all pages are rendered through `index.html`.

---

## 5. Model & Hardware Requirements (Task 3)

### 5.1 Hugging Face Model Footprint
- **Model Checkpoint:** `KRLabsOrg/lettucedect-base-modernbert-en-v1`
- **Inspected Cache:** `C:\Users\shash\.cache\huggingface\hub\models--KRLabsOrg--lettucedect-base-modernbert-en-v1`
- **File Breakdown:**
  - `model.safetensors`: **598,439,784 bytes** (~570.7 MB)
  - `tokenizer.json`: **3,583,228 bytes** (~3.4 MB)
  - `tokenizer_config.json`: **20,840 bytes**
  - `config.json`: **1,271 bytes**
  - **Total Disk Footprint:** **~575 MB**

### 5.2 Computational & Memory Budget
- **Architecture:** ModernBERT Transformer Token Classifier (138 weight layers).
- **Inference Mode:** PyTorch evaluation mode (`eval()`) under `torch.no_grad()`.
- **Device Support:** Native CPU inference using x86_64 AVX2 / AVX-512 vector instructions.
- **RAM Footprint:**
  - Python baseline: ~80 MB
  - Model weights loaded: ~570 MB
  - PyTorch runtime & intermediate activations: ~600 - 800 MB
  - **Total Peak RAM Requirement:** **~1.5 GB to 2.0 GB**
- **Startup Loading Time:** 60 - 80 seconds on CPU on first cold start (weights deserialization and tokenizer instantiation). Subsequent inferences take **340 - 770 ms**.
- **Model Caching:** Model weights are cached locally in the Hugging Face cache directory (`~/.cache/huggingface/hub`). Once downloaded, subsequent restarts load from local disk without network calls.

---

## 6. Google Cloud Deployment Architecture Recommendation (Task 4)

We compared the two primary hosting paths on Google Cloud:

### 6.1 Architecture Comparison

| Evaluation Dimension | Google Cloud Run (Serverless) | Google Compute Engine (Virtual Machine) |
| :--- | :--- | :--- |
| **Model Cold-Start** | **Problematic:** Container cold starts take 60–80s to load ModernBERT on CPU, causing HTTP request timeouts unless `--min-instances=1` is pinned. | **Optimal:** Model loads once on VM boot; remains memory-resident 24/7. Zero request latency penalty. |
| **Container Size** | Large container image (~3.0 GB with PyTorch, CUDA-less torch, Transformers, and weights). | Standard Git clone on VM; native Python virtual environment. |
| **Frontend Co-location** | Requires separate service or multi-stage Nginx container. | Nginx on VM serves frontend static files (`dist/`) and proxies `/api` on the same IP. |
| **CORS Friction** | Cross-origin requests between Cloud Run and frontend domain. | **Zero CORS friction**; unified origin through Nginx reverse proxy. |
| **Cost Predictability** | Free tier for low invocations, but `--min-instances=1` costs ~$25–35/month continuously. | `e2-standard-2` costs ~$48/month (or preemptible/spot ~$15/month; free credits eligible). |
| **Complexity** | Higher (Dockerfile, Cloud Build, Container Registry, Cloud Run configs). | **Minimal:** Familiar Linux VM setup, systemd daemon, Nginx. |

### 6.2 Recommended Architecture: Single Compute Engine VM (`e2-standard-2`)

```
                          [ Client Browser ]
                                  │
                                  │ HTTPS (Port 443) / HTTP (Port 80)
                                  ▼
               ┌──────────────────────────────────────┐
               │   Google Cloud Compute Engine VM     │
               │   Instance: e2-standard-2            │
               │   OS: Ubuntu 22.04 LTS (x86_64)      │
               │   Specs: 2 vCPUs, 8 GB RAM, 30 GB SSD│
               ├──────────────────────────────────────┤
               │                                      │
               │             Nginx Web Server         │
               │   ┌──────────────────────────────┐   │
               │   │ /       --> /var/www/dist    │   │  (React Frontend)
               │   │ /api/*  --> 127.0.0.1:8000   │   │  (Proxy to Uvicorn)
               │   └──────────────────────────────┘   │
               │                  │                   │
               │                  ▼                   │
               │         FastAPI / Uvicorn            │
               │        (systemd service)             │
               │                  │                   │
               │                  ▼                   │
               │      LettuceDetect ModernBERT        │
               │      (Resident in 8 GB RAM)          │
               └──────────────────────────────────────┘
                                  │ (Optional)
                                  ▼
                     [ Supabase PostgreSQL DB ]
```

- **Machine Type:** `e2-standard-2` (2 vCPUs, 8 GB RAM, 30 GB standard persistent disk).
- **Operating System:** Ubuntu 22.04 LTS x86_64.
- **Frontend Serving:** Nginx serves compiled static files from `/var/www/halluguard/frontend/dist/`.
- **Backend Serving:** Systemd daemon runs Uvicorn on `127.0.0.1:8000`.
- **Unified Proxy:** Nginx routes API traffic directly to Uvicorn, avoiding all browser CORS restrictions.
- **HTTPS:** Managed free SSL via Let's Encrypt / Certbot (`certbot --nginx`).

---

## 7. Local Run Verification (Task 5)

The documented local development commands were inspected and validated:

### Backend Startup Command:
```powershell
Set-Location "F:\final project\HalluGuard\backend"
& "F:\final project\LettuceDetect\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- **Validation:** Verified. Python interpreter exists, `app.main:app` module is correctly exported, and default port 8000 is standard.

### Frontend Startup Command:
```powershell
Set-Location "F:\final project\HalluGuard\frontend"
npm run dev
```
- **Validation:** Verified. `frontend/package.json` defines `"dev": "vite"`, which launches the local development server at `http://localhost:5173`.

---

## 8. Identified Blockers & Configuration Requirements

### Hard Blockers:
- **NONE.** There are no architectural, licensing, or algorithmic barriers preventing deployment.

### Prerequisites to Resolve for Deployment:
1. **`requirements.txt` Update:** Add `python-multipart>=0.0.9` to `backend/requirements.txt`.
2. **Submodule Deployment Strategy:** Ensure the deployment script or VM setup instructions clone both `HalluGuard` and `LettuceDetect` into adjacent directories and execute `pip install -e ../LettuceDetect`.
3. **Frontend API URL Binding:** Set `VITE_API_BASE_URL=""` for Nginx reverse-proxy deployment (or set the external server IP) before running the final production `npm run build`.
4. **Firewall & Network Configuration:** Allow TCP ingress on ports `80` (HTTP) and `443` (HTTPS) on Google Cloud VPC firewall.

---

## 9. Next Steps for Phase 5, Step 2

With the deployment readiness inspection complete, the following sequence is recommended for Phase 5 Step 2:

1. **Configuration Hygiene:**
   - Update `backend/requirements.txt` to include `python-multipart`.
   - Update `frontend/.env.production` for production API base URL mapping.
2. **Deployment Artifact Preparation:**
   - Generate unified deployment scripts (`setup_vm.sh`, `halluguard.service`, `nginx.conf`).
   - Create step-by-step Google Cloud Compute Engine provisioning guide.
3. **Staging / Verification:**
   - Verify deployment scripts locally or via automated container test before cloud rollout.

---

## 10. Audit & Compliance Statement

- No source files in `backend/`, `frontend/`, or `LettuceDetect/` were altered during this inspection.
- No packages were installed or removed.
- Model weights, cache files, and thresholds remain strictly preserved.
- No cloud resources were created or billed.

