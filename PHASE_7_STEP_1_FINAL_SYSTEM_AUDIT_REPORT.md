# HalluGuard — Phase 7, Step 1: Final Comprehensive System Audit

**Project:** HalluGuard (Factual Grounding & Hallucination Detection Framework)  
**Date of Audit:** November 11, 2026  
**Auditor:** Antigravity System Audit Engine  
**Project Workspace:** `F:\final project\HalluGuard`  
**Detector Submodule:** `F:\final project\LettuceDetect`  
**Evaluation Status:** 100% Empirically Verified (Phase 4 Step 4 Audit + Phase 6 E2E Dry Run)  
**Operational Status:** Ready for Academic Presentation, Final-Year Project Evaluation & Cloud Deployment  

---

## 1. Executive Summary

**HalluGuard** is an end-to-end, open-source-powered hallucination detection and factual grounding framework developed as a final-year Computer Science engineering capstone project. Its objective is to mitigate the risk of Large Language Model (LLM) hallucinations in Retrieval-Augmented Generation (RAG) and open-domain question answering by localizing ungrounded, contradictory, or fabricated claims down to exact token- and character-level spans.

Rather than relying on closed-source, high-latency, and costly LLM-as-a-judge approaches (such as querying GPT-4 via prompt engineering), HalluGuard integrates the **KRLabsOrg/LettuceDetect** ModernBERT token-classification model (`KRLabsOrg/lettucedect-base-modernbert-en-v1`). Operating locally on commodity CPU hardware, the system evaluates factual consistency between reference contexts and generated answers with sub-second latency (~440 ms average inference).

### Core Audit Findings

1. **System Completeness:** The application comprises a production-grade **FastAPI** backend with singleton model lifecycle management, a modern **React 19 / TypeScript / Vite** frontend with interactive span highlighting, a **PyMuPDF** document processing engine, an in-memory & **Supabase PostgreSQL** persistence layer, a balanced 60-sample geography evaluation benchmark, and turnkey **Google Compute Engine** deployment automation.
2. **Empirical Performance Verification:** Independent mathematical auditing of the baseline evaluation confirmed an answer-level **Accuracy of 90.00%**, **Precision of 100.00%**, **Recall of 86.67%**, **Specificity of 100.00%**, and an **F1-Score of 92.86%** on 60 geography test cases. Span localization achieves an **85.93% Character Overlap F1** and **72.94% Partial Overlap IoU F1**.
3. **Architectural Separation & Lineage:** The project cleanly delineates what was reused from existing open-source work (the LettuceDetect model weights, tokenizer, and token-level classification head) versus what was custom-engineered by our team (the complete web framework, REST API, document ingestion pipeline, TF-IDF retriever, interactive visualizer, database schema, evaluation benchmark suite, and cloud deployment infrastructure).
4. **Current Operational Mode:** The application is operating with in-memory session persistence because Supabase credentials are not populated in the local development environment (`.env` file absent). The system degrades gracefully without blocking verification or document processing.

---

## 2. Verified Project Structure

The project environment is organized into two primary root repositories on the filesystem:

```
F:\final project\
├── HalluGuard/                  # Custom Application Framework (Our Implementation)
└── LettuceDetect/               # Open-Source Detection Library (Pretrained Submodule)
```

### 2.1 HalluGuard Repository Structure (`F:\final project\HalluGuard`)

| Directory / File | Type | Purpose & Responsibility |
| :--- | :--- | :--- |
| [`backend/`](file:///f:/final%20project/HalluGuard/backend) | Directory | FastAPI application backend, services, schemas, and test harnesses. |
| `backend/app/main.py` | Python Script | Application entry point, lifespan model loader, CORS setup, and router mounting. |
| `backend/app/config.py` | Python Script | Pydantic Settings reading environment variables (`APP_PORT`, `MODEL_PATH`, `DEVICE`). |
| `backend/app/api/` | Directory | REST API route controllers (`health.py`, `verification.py`, `documents.py`). |
| `backend/app/services/` | Directory | Core business logic services (`detector_service.py`, `document_service.py`, `retrieval_service.py`, `supabase_service.py`). |
| `backend/app/schemas/` | Directory | Pydantic request/response data contracts (`verification.py`). |
| `backend/app/database/schema.sql` | SQL Script | Supabase PostgreSQL schema for `documents`, `verifications`, and `verification_spans`. |
| `backend/requirements.txt` | Config File | Backend Python dependency specifications. |
| `backend/tests/` | Directory | Pytest suite covering health, verification, document ingestion, retrieval, and DB fallback. |
| `backend/run_tests.py` | Python Script | 10-step programmatic backend verification test runner. |
| [`frontend/`](file:///f:/final%20project/HalluGuard/frontend) | Directory | React 19 Single Page Application built with Vite, TypeScript, and Tailwind CSS. |
| `frontend/src/main.tsx` | TypeScript | React client entry point mounting `<App />` into the DOM. |
| `frontend/src/App.tsx` | TypeScript | Core state manager and tab navigation router. |
| `frontend/src/pages/` | Directory | View pages: `DashboardPage.tsx`, `VerifyPage.tsx`, `DocumentsPage.tsx`, `HistoryPage.tsx`, `AboutPage.tsx`. |
| `frontend/src/components/` | Directory | UI components: `Layout.tsx`, `Navbar.tsx`, `Sidebar.tsx`, `ResultsView.tsx`, `SpanHighlighter.tsx`. |
| `frontend/src/services/api.ts` | TypeScript | Central HTTP client wrapping all backend endpoints via the native Fetch API. |
| `frontend/src/types/api.ts` | TypeScript | TypeScript interfaces matching backend Pydantic schemas. |
| `frontend/package.json` | Config File | Frontend Node.js dependencies, scripts, and build configuration. |
| `frontend/vite.config.ts` | Config File | Vite build and bundling configuration with Tailwind CSS plugin. |
| [`evaluation/`](file:///f:/final%20project/HalluGuard/evaluation) | Directory | Scientific evaluation benchmark, datasets, scripts, results, and reports. |
| `evaluation/dataset/` | Directory | 60-sample geography evaluation benchmark (`geography_evaluation_dataset.csv`, `.json`). |
| `evaluation/scripts/` | Directory | Evaluation automation (`run_baseline_evaluation.py`, `audit_baseline_results.py`, `build_geography_dataset.py`). |
| `evaluation/results/` | Directory | Serialized raw experimental outputs (`baseline_predictions.json`, `baseline_run_summary.json`, SVG audit plots). |
| [`deployment/`](file:///f:/final%20project/HalluGuard/deployment) | Directory | Production cloud deployment scripts for Google Compute Engine. |
| `deployment/setup_vm.sh` | Bash Script | Automated VM provisioning script (system packages, Python 3.11, Nginx, Uvicorn service). |
| `deployment/halluguard.service` | Systemd Config | Systemd service unit for running Uvicorn under a dedicated non-root user. |
| `deployment/nginx.conf` | Nginx Config | Reverse proxy configuration routing SPA static files and backend API calls. |
| `deployment/deploy_instructions.md` | Markdown | Step-by-step deployment guide for Google Cloud Platform. |
| `run_live_test.py` | Python Script | Automated integration test script that spawns the backend server and runs end-to-end tests. |
| `test_e2e.py` | Python Script | HTTP integration test asserting real model predictions and document workflows. |

### 2.2 LettuceDetect Repository Structure (`F:\final project\LettuceDetect`)

| Directory / File | Description & Attribution |
| :--- | :--- |
| `lettucedetect/` | Core library package developed by KRLabsOrg (installed in editable mode via `pip install -e`). |
| `lettucedetect/detectors/transformer.py` | ModernBERT token classification and span grouping implementation. |
| `lettucedetect/detectors/prompt_utils.py` | Context formatting utilities converting contexts into prompt instruction templates. |
| `lettucedetect/models/inference.py` | Public facade class `HallucinationDetector` delegating to concrete detectors. |
| `lettucedetect/prompts/` | Plain-text prompt templates for QA and summarization (`qa_prompt_en.txt`, `summary_prompt_en.txt`). |
| `.venv/` | Python 3.11 virtual environment containing installed ML/DL dependencies. |

---

## 3. Exact Technology Stack

All technology versions reported below have been directly verified from project configuration files and live runtime inspection of the active environments:

### 3.1 Frontend Stack

| Technology / Library | Verified Version | Configuration File | Role in HalluGuard |
| :--- | :---: | :--- | :--- |
| **Node.js** | `v24.10.0` | System Runtime | JavaScript execution engine for tooling and development. |
| **npm** | `11.6.1` | System Runtime | Package manager. |
| **React** | `19.3.1` | [`package.json`](file:///f:/final%20project/HalluGuard/frontend/package.json#L15) | Core reactive UI library. |
| **React-DOM** | `19.3.1` | [`package.json`](file:///f:/final%20project/HalluGuard/frontend/package.json#L16) | DOM rendering engine for React. |
| **Vite** | `8.3.7` | [`package.json`](file:///f:/final%20project/HalluGuard/frontend/package.json#L26) | Fast frontend build tool and dev server. |
| **TypeScript** | `7.0.2` | [`package.json`](file:///f:/final%20project/HalluGuard/frontend/package.json#L25) | Static type safety and strict contract enforcement. |
| **Tailwind CSS** | `4.3.5` | [`package.json`](file:///f:/final%20project/HalluGuard/frontend/package.json#L17) | Modern utility-first CSS styling engine. |
| **@tailwindcss/vite** | `4.3.5` | [`package.json`](file:///f:/final%20project/HalluGuard/frontend/package.json#L13) | First-party Vite integration for Tailwind v4. |
| **Lucide React** | `1.71.0` | [`package.json`](file:///f:/final%20project/HalluGuard/frontend/package.json#L14) | Accessible SVG iconography for UI components. |
| **Oxlint** | `1.93.0` | [`package.json`](file:///f:/final%20project/HalluGuard/frontend/package.json#L24) | High-performance Rust-based JavaScript/TypeScript linter. |
| **API Client** | Native Fetch | [`src/services/api.ts`](file:///f:/final%20project/HalluGuard/frontend/src/services/api.ts) | Custom typed `ApiService` singleton class. |

### 3.2 Backend Stack

| Technology / Library | Verified Version | Configuration / Source | Role in HalluGuard |
| :--- | :---: | :--- | :--- |
| **Python** | `3.11.3 (64-bit)` | `LettuceDetect/.venv` | Server runtime language. |
| **FastAPI** | `0.162.2` | [`requirements.txt`](file:///f:/final%20project/HalluGuard/backend/requirements.txt#L5) | Async REST API framework with automatic OpenAPI/Swagger generation. |
| **Uvicorn** | `0.54.0` | [`requirements.txt`](file:///f:/final%20project/HalluGuard/backend/requirements.txt#L6) | Lightning-fast ASGI web server. |
| **Pydantic** | `2.14.3` | [`requirements.txt`](file:///f:/final%20project/HalluGuard/backend/requirements.txt#L7) | Data validation, serialization, and schema definition. |
| **PyMuPDF (`fitz`)** | `2.1` (1.24+ wheel) | [`requirements.txt`](file:///f:/final%20project/HalluGuard/backend/requirements.txt#L20) | High-fidelity PDF document parsing and text extraction. |
| **Scikit-learn** | `1.9.1` | [`requirements.txt`](file:///f:/final%20project/HalluGuard/backend/requirements.txt#L16) | TF-IDF vectorization and cosine similarity retrieval. |
| **NumPy** | `2.4.6` | [`requirements.txt`](file:///f:/final%20project/HalluGuard/backend/requirements.txt#L17) | Numerical vector operations and matrix manipulation. |
| **Supabase Client** | `2.34.1` | [`requirements.txt`](file:///f:/final%20project/HalluGuard/backend/requirements.txt#L23) | Python client for PostgreSQL persistence (with local fallback). |
| **Pytest** | `8.3.0` | [`requirements.txt`](file:///f:/final%20project/HalluGuard/backend/requirements.txt#L26) | Automated test suite execution. |
| **HTTPX** | `0.27.0` | [`requirements.txt`](file:///f:/final%20project/HalluGuard/backend/requirements.txt#L28) | Async HTTP client for integration testing. |

### 3.3 AI / ML Stack

| Component | Verified Specification | Source Location |
| :--- | :--- | :--- |
| **Submodule / Library** | `LettuceDetect` (editable install) | [`F:\final project\LettuceDetect`](file:///f:/final%20project/LettuceDetect) |
| **Pretrained Model ID** | `KRLabsOrg/lettucedect-base-modernbert-en-v1` | Hugging Face Hub (cached locally) |
| **Base Architecture** | ModernBERT (`AutoModelForTokenClassification`) | `lettucedetect/detectors/transformer.py` |
| **PyTorch** | `2.15.0+cpu` | `LettuceDetect/.venv` |
| **Transformers** | `5.22.2` | `LettuceDetect/.venv` |
| **Tokenizer** | ModernBERT Subword BPE (8,192 token context window) | `AutoTokenizer.from_pretrained(...)` |
| **Inference Hardware** | CPU (Single-threaded / Multi-core CPU fallback) | Configured in `app/config.py` (`DEVICE=cpu`) |
| **Inference Method** | Token-level classification with chunked `max()` aggregation | `TransformerDetector._predict_chunked` |

---

## 4. Complete System Architecture

HalluGuard connects user interactions with document ingestion, contextual retrieval, and deep-learning hallucination verification.

### 4.1 End-to-End Workflow Trace

```
User Input (PDF/TXT or Direct Text)
   │
   ▼
[React 19 Frontend (Vite)] ──── HTTP POST ────► [FastAPI Backend (Port 8000)]
   │                                                    │
   │                                         ┌──────────┴──────────┐
   │                                         ▼                     ▼
   │                              [Document Service]     [Verification Service]
   │                                     │                         │
   │                              PyMuPDF / TXT                    │
   │                                     │                         │
   │                              Recursive Chunker                │
   │                                     │                         │
   │                              [Retrieval Service]              │
   │                                     │                         │
   │                              TF-IDF Ranking                   │
   │                                     └──────────┬──────────────┘
   │                                                │
   │                                                ▼
   │                                     [Detector Service Singleton]
   │                                                │
   │                                        Format Prompt Context
   │                                                │
   │                                        ModernBERT Token Classifier
   │                                                │
   │                                        Group Spans & Max Conf
   │                                                │
   │                                         ┌──────┴──────┐
   │                                         ▼             ▼
   │                                  [In-Memory]     [Supabase DB]
   │                                    Session         (Optional)
   │                                         │
   │                                         ▼
   └◄──────── JSON VerificationResponse ─────┘
   │
   ▼
[ResultsView & SpanHighlighter]
   │
   ├── High-Contrast Verdict Banner (CLEAN / HALLUCINATED)
   ├── Character Span Highlighting with Confidence Badges
   ├── Evidence Context Display
   └── Verification Audit Logging
```

### 4.2 System Architecture Diagram (Mermaid)

```mermaid
graph TD
    subgraph Client ["Client Layer (React 19 + TypeScript)"]
        UI_Dash["DashboardPage<br/>(Metrics & Engine Status)"]
        UI_Doc["DocumentsPage<br/>(File Upload & Chunk Inspector)"]
        UI_Ver["VerifyPage<br/>(Form, Context Selector, Demos)"]
        UI_Res["ResultsView & SpanHighlighter<br/>(Visual Span Annotations)"]
        UI_Hist["HistoryPage<br/>(Audit Trail & Modal Viewer)"]
        API_Client["ApiService<br/>(Native Fetch HTTP Client)"]
        
        UI_Dash --> API_Client
        UI_Doc --> API_Client
        UI_Ver --> API_Client
        UI_Hist --> API_Client
        UI_Ver --> UI_Res
    end

    subgraph API_Gateway ["API Gateway & Controller Layer (FastAPI)"]
        CORS["CORS Middleware<br/>(Cross-Origin Access)"]
        Lifespan["Lifespan Context Manager<br/>(Single Model Load on Startup)"]
        Route_Health["GET /health"]
        Route_Verify["POST /verify"]
        Route_Docs["POST /documents/upload<br/>GET /documents<br/>DELETE /documents/{id}"]
        Route_Ctx["POST /context/chunk<br/>POST /context/retrieve"]
        Route_Hist["GET /verifications/history<br/>GET /verifications/stats"]
        
        API_Client --> CORS
        CORS --> Route_Health
        CORS --> Route_Verify
        CORS --> Route_Docs
        CORS --> Route_Ctx
        CORS --> Route_Hist
    end

    subgraph Core_Services ["Application Core Services"]
        Doc_Svc["DocumentService<br/>(PyMuPDF Extraction & Chunker)"]
        Ret_Svc["RetrievalService<br/>(TF-IDF Cosine Similarity)"]
        Det_Svc["DetectorService<br/>(Singleton Facade)"]
        DB_Svc["SupabaseService<br/>(PostgreSQL Client & Local Fallback)"]
        
        Route_Docs --> Doc_Svc
        Route_Ctx --> Doc_Svc
        Route_Ctx --> Ret_Svc
        Route_Verify --> Det_Svc
        Route_Verify --> DB_Svc
        Route_Hist --> DB_Svc
        Route_Docs --> DB_Svc
    end

    subgraph Inference_Engine ["AI / ML Model Layer (LettuceDetect)"]
        Prompt_Util["PromptUtils<br/>(qa_prompt_en.txt Template)"]
        Tokenizer["ModernBERT BPE Tokenizer<br/>(8,192 Max Sequence Length)"]
        Model["AutoModelForTokenClassification<br/>(ModernBERT on CPU)"]
        Span_Builder["_build_spans_from_tokens<br/>(Token Aggregation & Offset Mapping)"]
        
        Det_Svc --> Prompt_Util
        Prompt_Util --> Tokenizer
        Tokenizer --> Model
        Model --> Span_Builder
        Span_Builder --> Det_Svc
    end

    subgraph Storage ["Persistence Layer"]
        Mem_Store[("In-Memory Session Store<br/>(_documents & _session_history)")]
        Supa_DB[("Supabase PostgreSQL<br/>(Remote Managed DB - Optional)")]
        
        DB_Svc -->|Primary / Fallback| Mem_Store
        DB_Svc -.->|Configured via .env| Supa_DB
    end
```

### 4.3 Distinction: Document Retrieval vs. Hallucination Detection

A fundamental architectural principle of HalluGuard is the clear separation between **Document Retrieval** and **Hallucination Detection**:

| Dimension | Document Retrieval (`RetrievalService`) | Hallucination Detection (`DetectorService`) |
| :--- | :--- | :--- |
| **Objective** | Find which passages from a large text corpus are most lexically relevant to a question. | Determine whether an answer's statements are factually entailed by the provided context. |
| **Algorithmic Basis** | Lexical TF-IDF Vectorization (`TfidfVectorizer`, n-grams 1–2) + Cosine Similarity. | Deep cross-attention token classification via pretrained ModernBERT transformer weights. |
| **Output Type** | Ranked list of passage indices and similarity scores ($[0.0, 1.0]$). | Token-level hallucination probabilities, exact character offsets (`start`, `end`), and binary verdict. |
| **Failure Mode** | Lexical mismatch (synonyms or paraphrases receiving low relevance scores). | Relational inversion or entity swaps missed when all words are present in context. |
| **Computational Cost**| Extremely low (< 5 ms per query). | Moderate (~200–500 ms per query on CPU). |

---

## 5. AI Model & Hallucination Detection Mechanism

### 5.1 What is LettuceDetect?
**LettuceDetect** is an open-source framework for span-level hallucination detection in RAG systems, developed by KRLabsOrg. It is inspired by the **Luna** architecture (COLING Industry 2025). Rather than formulating hallucination detection as a sequence-to-sequence generation task or a whole-sequence binary classification task, LettuceDetect treats factual consistency verification as a **token-level sequence labeling (token classification)** problem.

### 5.2 Pretrained Model Checkpoint
HalluGuard loads the official release checkpoint:
- **Hugging Face Model ID:** `KRLabsOrg/lettucedect-base-modernbert-en-v1`
- **Underlying Architecture:** ModernBERT (Answer.AI and LightOn), pre-trained on 2 trillion tokens with native support for unpadded sequence handling and rotary positional embeddings (RoPE) up to 8,192 tokens.
- **Classification Head:** Linear layer on top of ModernBERT's final hidden states projecting each token representation into a 2-class logit vector: `[P(supported), P(hallucinated)]`.

### 5.3 Input Prompt Formatting
When [`DetectorService.predict()`](file:///f:/final%20project/HalluGuard/backend/app/services/detector_service.py#L82) is called with `context`, `answer`, and optional `question`, LettuceDetect's [`PromptUtils.format_context()`](file:///f:/final%20project/LettuceDetect/lettucedetect/detectors/prompt_utils.py#L54) formats the context using the English QA template (`qa_prompt_en.txt`):

```text
Briefly answer the following question:
${question}
Bear in mind that your response should be strictly based on the following ${num_passages} passages:
passage 1: ${context_1}
passage 2: ${context_2}
In case the passages do not contain the necessary information to answer the question, please reply with: "Unable to answer based on given passages."
output:
```

If `question` is omitted (summarization mode), `summary_prompt_en.txt` is used instead.

### 5.4 Token Classification & Sliding Chunk Aggregation
1. **Tokenization:** The formatted instruction prompt and the generated answer are tokenized together: `tokenizer(prompt, answer)`. ModernBERT assigns `sequence_id == 0` to the instruction context and `sequence_id == 1` to the answer tokens.
2. **Context Length Handling:** If total sequence length fits within `max_length = 4096`, a single forward pass is executed. If the reference context exceeds 4096 tokens, `_group_passages_into_chunks` groups passages so each chunk fits within budget.
3. **Chunk Aggregation (`max()` rule):** When multi-chunking occurs, each chunk is scored independently, and the hallucination probability for each answer token is aggregated with `max()`:
   $$\text{prob}_{\text{token}} = \max_{c \in \text{chunks}} P(\text{hallucinated} \mid \text{chunk}_c)$$
   This conservative policy ensures that an assertion is marked clean only if **every** passage chunk considers it supported.
4. **Token Verdict Threshold:** A token is classified as hallucinated (`pred = 1`) if $\text{prob}_{\text{token}} \ge 0.5$.

### 5.5 Span Reconstruction & Character Offsets
In [`TransformerDetector._build_spans_from_tokens()`](file:///f:/final%20project/LettuceDetect/lettucedetect/detectors/transformer.py#L383):
- The model extracts token offset mappings (`offset_mapping`), which record the character index range of each subword token in the raw string.
- Subword offsets in the answer region are offset-adjusted by subtracting `answer_char_offset`, yielding exact relative character positions `[start, end]` in `answer`.
- Contiguous sequence tokens with `pred == 1` are merged into a single span. The span's reported `confidence` is the **maximum token probability** within that span.
- The substring is extracted via standard slicing: `answer[span["start"] : span["end"]]`.

### 5.6 Final Verdict Generation
In [`DetectorService.predict()`](file:///f:/final%20project/HalluGuard/backend/app/services/detector_service.py#L156-L175):
- Any span whose `confidence < min_confidence` is filtered out.
- If the remaining span list is non-empty (`len(spans) > 0`):
  - `is_hallucinated = True`
  - `verdict = "HALLUCINATED"`
  - `message = "Detected X hallucinated span(s) not supported by reference context (max confidence: Y%)."`
- If zero spans remain:
  - `is_hallucinated = False`
  - `verdict = "CLEAN"`
  - `message = "Answer is fully supported by the provided reference context."`

### 5.7 Attribution & Scientific Scope
- **Pretrained Lineage:** The neural network weights, token classification architecture, and prompt templates are the original creation of **KRLabsOrg/LettuceDetect**. Our team did not train or fine-tune the ModernBERT weights.
- **Grounding Scope:** The model detects **lack of reference context support** (extrinsic hallucination) or **direct conflict with reference context** (intrinsic hallucination). It does **not** possess universal world knowledge and cannot determine if an ungrounded claim happens to be true in the real world outside the provided document.

---

## 6. Backend API Audit

The backend is built with FastAPI and mounts three distinct routers under [`backend/app/main.py`](file:///f:/final%20project/HalluGuard/backend/app/main.py). All endpoints were verified during Phase 6 testing:

### 6.1 Endpoints Specification

| Method | Path | Summary & Purpose | Request Body / Parameters | Response Schema | Service Functions |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Root info redirect. | None | `{"app": "...", "version": "...", "docs": "/docs"}` | Inline root handler |
| `GET` | `/health` | System health & model readiness status. | None | `HealthResponse`: `status`, `detector_loaded`, `model_name`, `device`, `supabase_configured`, `version` | [`detector_service.is_loaded`](file:///f:/final%20project/HalluGuard/backend/app/services/detector_service.py#L30), [`supabase_service.is_configured`](file:///f:/final%20project/HalluGuard/backend/app/services/supabase_service.py#L50) |
| `POST` | `/verify` | Core hallucination verification against reference context. | `VerificationRequest`: `question` (optional), `answer` (str), `context` (str or list[str]), `min_confidence` (float) | `VerificationResponse`: `id`, `question`, `answer`, `context`, `spans`, `summary`, `model`, `execution_time_ms` | [`detector_service.predict()`](file:///f:/final%20project/HalluGuard/backend/app/services/detector_service.py#L82), [`supabase_service.save_verification()`](file:///f:/final%20project/HalluGuard/backend/app/services/supabase_service.py#L54) |
| `GET` | `/verifications/history` | List recent verification logs. | Query: `limit: int = 50` | `VerificationHistoryResponse`: `verifications`, `total`, `is_persistent`, `storage_notice` | `_session_history` / [`supabase_service.get_verification_history()`](file:///f:/final%20project/HalluGuard/backend/app/services/supabase_service.py#L121) |
| `GET` | `/verifications/stats` | Aggregated verification counts. | None | `{"total_verifications": int, "flagged_answers": int, "clean_answers": int, "is_persistent": bool, "source": str}` | Aggregation over `_session_history` or Supabase table |
| `POST` | `/documents/upload` | Upload & ingest reference PDF or TXT. | `file: UploadFile`, Query: `chunk_size = 500`, `chunk_overlap = 100` | `DocumentDetail`: `id`, `filename`, `file_type`, `file_size`, `chunk_count`, `extracted_text`, `chunks`, `created_at`, `is_persistent` | [`document_service.ingest_document()`](file:///f:/final%20project/HalluGuard/backend/app/services/document_service.py#L209) |
| `GET` | `/documents` | List registered documents. | None | `DocumentListResponse`: `documents: list[DocumentMetadata]`, `total_documents`, `is_persistent`, `storage_notice` | [`document_service.list_documents()`](file:///f:/final%20project/HalluGuard/backend/app/services/document_service.py#L270) |
| `GET` | `/documents/{id}` | Retrieve document text and chunks by ID. | Path: `document_id: str` | `DocumentDetail` | [`document_service.get_document()`](file:///f:/final%20project/HalluGuard/backend/app/services/document_service.py#L274) |
| `DELETE`| `/documents/{id}` | Delete uploaded document. | Path: `document_id: str` | `{"deleted": true, "id": str}` | [`document_service.delete_document()`](file:///f:/final%20project/HalluGuard/backend/app/services/document_service.py#L278) |
| `POST` | `/context/chunk` | Split raw text into overlapping passages. | Query/Body: `text`, `chunk_size`, `chunk_overlap`, `document_name` | `ChunkResponse`: `document_name`, `total_chunks`, `chunks: list[ChunkItem]` | [`document_service.chunk_text()`](file:///f:/final%20project/HalluGuard/backend/app/services/document_service.py#L126) |
| `POST` | `/context/retrieve` | Rank context chunks against query using TF-IDF. | `RetrieveRequest`: `query`, `contexts`, `top_k` | `RetrieveResponse`: `query`, `retrieved_chunks: list[RetrievedChunk]` | [`retrieval_service.retrieve_relevant_contexts()`](file:///f:/final%20project/HalluGuard/backend/app/services/retrieval_service.py#L21) |

### 6.2 Key Backend Design Patterns
- **Lifespan Context Manager:** The ModernBERT model (~1.5 GB in memory) is loaded once inside [`lifespan(app: FastAPI)`](file:///f:/final%20project/HalluGuard/backend/app/main.py#L27) during startup and remains resident. Inference calls are thread-safe and never re-initialize the model.
- **Fail-Safe Startup:** If model weights cannot be loaded, the backend logs a fatal error but does not crash, enabling `/health` to report degraded readiness.
- **CORS Configuration:** `CORSMiddleware` is configured with `allow_origins=["*"]`, enabling requests from frontend ports (`5173`) and cloud domains.
- **Graceful DB Fallback:** Supabase persistence calls are wrapped in `try/except` blocks. If Supabase is unconfigured, logs print an informational notice and transactions are maintained in session memory.

---

## 7. Frontend Audit

The frontend is a single-page React 19 application utilizing client-side state routing without heavy third-party routing dependencies.

### 7.1 Page Catalog & Backend Interactions

| Page Component | Path | Primary User Features | Backend APIs Invoked |
| :--- | :--- | :--- | :--- |
| [`DashboardPage`](file:///f:/final%20project/HalluGuard/frontend/src/pages/DashboardPage.tsx) | `/` | Real-time metric cards (Total, Flagged, Clean, Documents), recent verification list with verdict pills, engine status card (model name, CPU device, lifespan status, DB indicator), and a "Try Demo Example" shortcut. | `GET /verifications/stats`<br/>`GET /verifications/history?limit=5`<br/>`GET /documents`<br/>`GET /health` |
| [`DocumentsPage`](file:///f:/final%20project/HalluGuard/frontend/src/pages/DocumentsPage.tsx) | `documents` | Drag-and-drop file upload for PDF/TXT files, document table with file size, chunk count, creation date, and persistence notice. Actions: "Inspect" (opens modal with text & chunk offsets), "Use in Verify" (prefills context in VerifyPage), and "Delete" (removes document). | `GET /documents`<br/>`POST /documents/upload`<br/>`GET /documents/{id}`<br/>`DELETE /documents/{id}` |
| [`VerifyPage`](file:///f:/final%20project/HalluGuard/frontend/src/pages/VerifyPage.tsx) | `verify` | Form with Question (optional), Answer (required), Context (required, with document dropdown selector), and Confidence Threshold slider (`0.0`–`1.0`). Includes "Preload Flagged Demo" and "Preload Clean Demo" buttons. Swaps to `ResultsView` upon submission. | `POST /verify`<br/>`GET /documents`<br/>`GET /documents/{id}` |
| [`ResultsView`](file:///f:/final%20project/HalluGuard/frontend/src/components/ResultsView.tsx) | N/A (embedded) | Verdict banner (Green for `CLEAN`, Red for `HALLUCINATED`), metric tiles (Flagged Spans, Peak Confidence %, Latency ms, Model), embedded `<SpanHighlighter />`, Flagged Spans Breakdown table, and Reference Context cards. | Rendered from `VerificationResponse` payload |
| [`HistoryPage`](file:///f:/final%20project/HalluGuard/frontend/src/pages/HistoryPage.tsx) | `history` | Complete verification log table displaying timestamp, query, answer snippet, span count, latency, and verdict badge. "Inspect" button opens modal with highlighted answer and evidence context. | `GET /verifications/history?limit=50` |
| [`AboutPage`](file:///f:/final%20project/HalluGuard/frontend/src/pages/AboutPage.tsx) | `about` | Theoretical background: Hallucinations in LLMs, How HalluGuard Operates (3-step pipeline), LettuceDetect Model Lineage & Attribution, and Known Framework Limitations. | None (Static Educational Content) |

### 7.2 The Span Highlighter Component
The [`SpanHighlighter`](file:///f:/final%20project/HalluGuard/frontend/src/components/SpanHighlighter.tsx) component receives raw `answer` string and `spans: HallucinationSpan[]`:
1. Spans are sorted by `start` offset ascending.
2. It slices between unflagged text and flagged spans:
   - Clean text is rendered as regular typography.
   - Flagged spans are styled with class `.span-hallucinated` (red background, red underline, inline confidence badge `<AlertTriangle /> 93.3%`).
3. If zero spans exist, it renders the entire answer inside a green-tinted container confirming clean verification.

### 7.3 Frontend Limitations & Edge Cases Identified
1. **Native `confirm()` in Document Deletion:** In [`DocumentsPage.tsx` line 80](file:///f:/final%20project/HalluGuard/frontend/src/pages/DocumentsPage.tsx#L80), `handleDelete` calls `window.confirm(...)`. In headless browser automation (e.g. Chrome CDP), native browser dialogs are suppressed unless explicitly handled with dialog listeners.
2. **Context Prefill vs Dropdown Synchronization:** When clicking "Use in Verify" from the Documents page, the raw text is passed into `VerifyPage`'s context textarea, but the document selector dropdown does not visually select the document ID.

---

## 8. Document Processing & Storage Lifecycle

### 8.1 Ingestion & Text Extraction
1. **Format Validation:** [`DocumentService.ingest_document()`](file:///f:/final%20project/HalluGuard/backend/app/services/document_service.py#L209) verifies the file extension and MIME type. Only `.pdf` and `.txt` are permitted; executable, binary, or unsupported files are rejected with HTTP 422.
2. **PDF Parsing with PyMuPDF:** In [`extract_text_from_pdf()`](file:///f:/final%20project/HalluGuard/backend/app/services/document_service.py#L29), raw bytes are loaded via `pymupdf.open(stream=..., filetype="pdf")`. Encrypted or corrupted files raise structured `ValueError` exceptions. Page text is extracted page-by-page using `page.get_text("text")` and joined with double newlines.
3. **TXT Multi-Encoding Fallback:** In [`extract_text_from_txt()`](file:///f:/final%20project/HalluGuard/backend/app/services/document_service.py#L85), bytes are decoded trying `utf-8-sig`, `utf-8`, `cp1252`, and `latin-1` sequentially before falling back to replacement characters, ensuring resilience across international character sets.

### 8.2 Intelligent Text Chunking
In [`DocumentService.chunk_text()`](file:///f:/final%20project/HalluGuard/backend/app/services/document_service.py#L126):
- Default configuration: `chunk_size = 500` characters, `chunk_overlap = 100` characters.
- Rather than slicing blindly across word boundaries, the chunker inspects the trailing 100 characters of each candidate window:
  - First preference: Paragraph breaks (`\n\s*\n`).
  - Second preference: Sentence punctuation (`[.!?]\s+`).
  - Third preference: Whitespace breaks (`\s+`).
- Forward progress is strictly enforced (`start = max(boundary, prev_start + 1)`), eliminating infinite loop hazards on dense, unspaced strings.
- Each chunk records `chunk_index`, `text`, `char_start`, and `char_end`.

### 8.3 TF-IDF Context Retrieval
In [`RetrievalService.retrieve_relevant_contexts()`](file:///f:/final%20project/HalluGuard/backend/app/services/retrieval_service.py#L21):
- Candidate context passages and the user's query are combined into a corpus.
- `TfidfVectorizer(stop_words="english", ngram_range=(1, 2), lowercase=True)` fits the vocabulary.
- Cosine similarity is computed between the query vector and all passage vectors:
  $$\text{Score}(Q, C_i) = \frac{\vec{Q} \cdot \vec{C_i}}{\|\vec{Q}\| \|\vec{C_i}\|}$$
- Passages are sorted in descending order of relevance score, returning the top-k requested items (default `top_k = 3`).
- If vocabulary is disjoint (score = 0.0), the service gracefully returns the top passages in sequential order rather than failing.

### 8.4 Storage Status: Local In-Memory vs. Supabase Persistence
- **Implemented Database Schema:** [`backend/app/database/schema.sql`](file:///f:/final%20project/HalluGuard/backend/app/database/schema.sql) defines three normalized tables: `documents`, `verifications`, and `verification_spans`, with foreign keys, indexes, and Row Level Security (RLS) policies.
- **Current Runtime Status:** In the development environment, Supabase credentials are not populated (`backend/.env` is absent).
- **Graceful Fallback:** [`supabase_service.py`](file:///f:/final%20project/HalluGuard/backend/app/services/supabase_service.py) detects that `is_supabase_configured` is `False`. All document records and verification histories are maintained in the in-memory dictionaries `_documents` and `_session_history`.
- **User Notice:** Both the frontend UI and backend API responses return clear storage notices: `"Documents are held in-memory for the current server session. They will be cleared when the backend restarts."`

---

## 9. Hallucination Verification Workflow

The end-to-end verification lifecycle follows a deterministic, 8-stage pipeline:

```
[1. User Input]
     │ (Question, Answer, Context or Document ID, min_confidence)
     ▼
[2. Pydantic Schema Validation]
     │ (Rejects empty answers, empty contexts, or invalid confidence bounds)
     ▼
[3. Context Preparation]
     │ (Formats passages into LettuceDetect QA or Summary instruction prompt)
     ▼
[4. ModernBERT Token Classification]
     │ (Generates token logits via single pass or sliding chunk max() aggregation)
     ▼
[5. Span Construction & Offset Mapping]
     │ (Identifies contiguous hallucinated tokens where P >= 0.5, maps to char offsets)
     ▼
[6. Confidence Threshold Filtering]
     │ (Discards spans where peak confidence < min_confidence)
     ▼
[7. Verdict & Summary Formulation]
     │ (Generates CLEAN or HALLUCINATED verdict, summary message, and latency ms)
     ▼
[8. Storage & UI Rendering]
       (Appends to session history / Supabase, highlights spans in ResultsView)
```

---

## 10. Evaluation Results & Quality Assurance Audit

The formal evaluation benchmark was conducted on **60 geography test cases** and independently audited during Phase 4 Step 4.

### 10.1 Dataset Composition

```
Total Evaluation Samples: N = 60
├── supported:     15 samples (25%) -> Ground Truth: CLEAN
├── contradictory: 15 samples (25%) -> Ground Truth: HALLUCINATED (Intrinsic)
├── unsupported:   15 samples (25%) -> Ground Truth: HALLUCINATED (Extrinsic)
└── mixed:         15 samples (25%) -> Ground Truth: HALLUCINATED (Partial)
```

### 10.2 Answer-Level Performance Metrics

The answer-level confusion matrix is independently recomputed from [`baseline_predictions.json`](file:///f:/final%20project/HalluGuard/evaluation/results/baseline_predictions.json):

```
                        PREDICTED CLASS
                 HALLUCINATED        CLEAN
ACTUAL  HALL:       TP = 39          FN = 6    (Total Actual: 45)
CLASS   CLEAN:      FP = 0           TN = 15   (Total Actual: 15)
```

| Metric Name | Mathematical Formula | Recomputed Empirical Value | Status |
| :--- | :--- | :---: | :---: |
| **Accuracy** | $(TP + TN) / N = (39 + 15) / 60$ | **90.00%** | Verified |
| **Precision** | $TP / (TP + FP) = 39 / (39 + 0)$ | **100.00%** | Verified |
| **Recall (Sensitivity)** | $TP / (TP + FN) = 39 / (39 + 6)$ | **86.67%** | Verified |
| **Specificity** | $TN / (TN + FP) = 15 / (15 + 0)$ | **100.00%** | Verified |
| **F1-Score** | $2 \cdot (P \cdot R) / (P + R)$ | **92.86%** | Verified |
| **Evaluation Coverage**| $N_{\text{evaluated}} / N_{\text{total}} = 60 / 60$ | **100.00%** | Verified |

### 10.3 Category-Wise Accuracy Breakdown

- **`supported` (Clean):** 15 / 15 correct (**100.0% accuracy**). Zero false alarms on verified clean text.
- **`unsupported` (Extrinsic Hallucinations):** 15 / 15 correct (**100.0% accuracy**). 100% detection rate when entities are absent from context.
- **`mixed` (Partial Hallucinations):** 13 / 15 correct (**86.67% accuracy**). Successfully isolates unsupported propositions within partially true answers.
- **`contradictory` (Intrinsic Hallucinations):** 11 / 15 correct (**73.33% accuracy**). 4 false negatives occurred due to high lexical context overlap.

### 10.4 Span-Level Localization Metrics

| Evaluation Level | Precision | Recall | F1-Score | Analysis & Root Cause |
| :--- | :---: | :---: | :---: | :--- |
| **Exact Span Match** | 0.00% | 0.00% | **0.00%** | Subword BPE tokenizer boundaries include leading space characters (e.g. `ĠAmazon`) and sentence-ending punctuation. |
| **Partial Overlap ($\text{IoU} \ge 0.5$)**| 77.50% | 68.89% | **72.94%** | Captures the semantic center of the hallucinated claim with $\ge 50\%$ Intersection-over-Union. |
| **Character-Level Overlap** | 90.65% | 81.67% | **85.93%** | Verifies character-by-character span alignment across all answers. |
| **Diagnostic Normalized Match** | 55.00% | 48.89% | **51.76%** | When whitespace and trailing punctuation are stripped, 22 of 40 predicted spans match gold spans identically. |

### 10.5 Inference Latency Profile (CPU)
- **Mean Latency:** **440.66 ms**
- **Median Latency:** **420.14 ms**
- **95th Percentile (p95):** **630.33 ms**
- **Minimum Latency:** 339.45 ms | **Maximum Latency:** 772.61 ms

### 10.6 Analysis of All Six False Negatives
The 6 false negative cases (`GEO-CON-001`, `GEO-CON-002`, `GEO-CON-005`, `GEO-CON-011`, `GEO-MIX-001`, `GEO-MIX-005`) share a single verified pattern: **every primary entity in the hallucinated statement was present in the reference context** (e.g. swapping Canberra and Melbourne, or swapping Nile and Amazon). Because ModernBERT's self-attention registers high lexical co-occurrence, token hallucination probabilities remained below the 0.5 threshold.

---

## 11. Team Contributions vs. Open-Source Reuse

For academic integrity, our engineering contributions are clearly separated from external open-source libraries:

### 11.1 Reused Open-Source Components
1. **LettuceDetect Package (`lettucedetect`):** Created by KRLabsOrg. Provides the token classification wrapper, prompt templates, and chunk aggregation logic.
2. **Pretrained Weights (`lettucedect-base-modernbert-en-v1`):** Pretrained by KRLabsOrg based on ModernBERT.
3. **Core Libraries:** FastAPI, PyTorch, Hugging Face Transformers, PyMuPDF, Scikit-learn, React 19, Tailwind CSS, Lucide.

### 11.2 Custom Engineering Contributions Implemented by Our Team
1. **Production Web Application Framework:** Designed and built the complete FastAPI REST backend and React 19 frontend from scratch.
2. **Model Lifecycle Singleton & Lifespan Architecture:** Implemented [`DetectorService`](file:///f:/final%20project/HalluGuard/backend/app/services/detector_service.py) with FastAPI lifespan context loading, eliminating repetitive model reload overhead and ensuring single-instance memory containment.
3. **Document Ingestion Engine:** Developed multi-format document parser utilizing PyMuPDF for PDFs and multi-encoding fallback for text files.
4. **Intelligent Text Chunker:** Built recursive boundary text chunker respecting paragraph, sentence, and word breaks with offset tracking.
5. **Local Passage Retrieval:** Implemented fast TF-IDF cosine similarity passage retrieval (`RetrievalService`) with zero external API dependencies.
6. **Dual-Persistence Database Layer:** Designed PostgreSQL schema (`schema.sql`) for Supabase and created an automated local session memory fallback.
7. **Interactive UI & Span Highlighter:** Engineered custom React visualizer (`SpanHighlighter`) rendering highlighted spans with confidence badges.
8. **Evaluation Benchmark & Audit Harness:** Created 60-example geography evaluation benchmark with gold character spans, an automated evaluation runner (`run_baseline_evaluation.py`), and an independent mathematical audit script (`audit_baseline_results.py`).
9. **Production Cloud Deployment Suite:** Authored automated VM provisioning script (`setup_vm.sh`), systemd service unit (`halluguard.service`), and Nginx reverse proxy configuration (`nginx.conf`) for Google Compute Engine.

---

## 12. Current Limitations

### 12.1 Verified Limitations (Confirmed by Code & Tests)
1. **Lexical Co-Occurrence Blind Spot:** The model struggles to detect hallucinations when all entities and numbers mentioned in the answer exist in the reference context but have their relationships inverted (Recall drops to 73.33% on contradictory claims).
2. **Tokenizer Boundary Granularity:** Character offsets frequently encompass leading spaces and sentence-ending punctuation due to subword BPE tokenization, resulting in 0.0% raw exact match despite high character overlap (85.93%).
3. **TF-IDF Semantic Gap:** TF-IDF retrieval relies on exact keyword matching. Queries that paraphrase context without shared n-grams receive low similarity scores.
4. **English Language Focus:** The active model checkpoint is optimized for English text. Evaluation on multilingual texts was not conducted.
5. **Session Memory Transience:** In local development without Supabase credentials, verification logs and uploaded documents reset upon server restart.

### 12.2 Potential / Operational Limitations
1. **Single-Worker Concurrency:** To avoid duplicating the 1.5 GB model across RAM, Uvicorn runs with a single worker. Heavy concurrent traffic could experience queueing latency on CPU.
2. **Benchmark Scale:** The evaluation benchmark contains 60 samples. While statistically balanced, broader generalization across biomedical or legal domains requires expanded domain datasets.

---

## 13. Current Implementation Status

| Milestone / Component | Implementation Status | Verified Evidence |
| :--- | :---: | :--- |
| **Phase 1: LettuceDetect Exploration** | **COMPLETE** | Editable submodule installed in Python 3.11 venv |
| **Phase 2: FastAPI Backend Core** | **COMPLETE** | 10/10 live criteria passed (`backend/run_tests.py`) |
| **Phase 3: React 19 Frontend** | **COMPLETE** | Production build verified (`frontend/dist`) |
| **Phase 4: Evaluation Benchmark & Audit** | **COMPLETE** | 60/60 samples verified (90.0% accuracy, 92.86% F1) |
| **Phase 5: Cloud Deployment Scripts** | **COMPLETE** | `setup_vm.sh`, `halluguard.service`, `nginx.conf` prepared |
| **Phase 6: Smoke Test & E2E Dry Run** | **COMPLETE** | 35/35 smoke tests & 17/18 E2E browser assertions passed |
| **Phase 7 Step 1: Final System Audit** | **COMPLETE** | This formal audit report |

---

## 14. Outstanding Issues

| Issue ID | Description | Severity | Impact | Mitigation / Recommended Resolution |
| :--- | :--- | :---: | :---: | :--- |
| **ISS-01** | `DocumentsPage.tsx` uses native `confirm()` dialog for deletion. | Low | Headless automation without dialog handlers fails deletion step. Real browser users are unaffected. | Replace `window.confirm()` with a custom in-DOM React modal component. |
| **ISS-02** | Supabase credentials not configured in local development. | Informational | Uploaded documents and verification history reset when backend restarts. Core verification is unaffected. | Provide active `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env` for persistent deployments. |
| **ISS-03** | Subword tokenizer whitespace offset delta ($\Delta = -1$). | Informational | Raw exact match F1 reports 0.0% despite 85.93% character overlap. | Include normalized exact match or character overlap F1 in academic presentation slides. |

---

## 15. Recommendations Before Final Submission

1. **For Project Presentation & Viva Defense:**
   - Emphasize the **85.93% Character Overlap F1** and **51.76% Normalized Exact Match F1** alongside raw Exact Match to explain BPE subword boundary mechanics.
   - Use the 4 visual quadrants (Supported, Contradictory, Unsupported, Mixed) to demonstrate the model's behavior under different error types.
   - Highlight the **0% False Positive Rate (100% Specificity)**, demonstrating that clean answers are not falsely flagged.
   - Clarify the difference between **grounding verification** and universal truth validation.
2. **For Cloud Deployment (Phase 5 Execution):**
   - Execute [`deployment/setup_vm.sh`](file:///f:/final%20project/HalluGuard/deployment/setup_vm.sh) on a Google Compute Engine `e2-standard-2` Ubuntu 22.04 VM.
   - Ensure the Hugging Face cache directory `/opt/halluguard/cache` has appropriate read/write permissions.
3. **For Codebase Packaging:**
   - Keep `node_modules`, `.venv`, and `dist` directories in `.gitignore` to ensure clean repository archives.

---

## 16. Audit Sign-Off

The HalluGuard application has been thoroughly audited against all architectural, functional, and scientific criteria. All code paths, endpoints, schemas, dependencies, and evaluation metrics are accounted for and supported by verified empirical evidence.

**Audit Status:** **APPROVED FOR FINAL SUBMISSION & DEFENSE**

