# HalluGuard — Phase 5, Step 2: Deployment Preparation Report

**Date:** 2026-11-10  
**Phase:** Phase 5 — Deployment (Step 2: Deployment Script & Configuration Preparation)  
**Status:** Completed Successfully (All Scripts, Units, and Configs Prepared & Validated)  
**Target Environment:** Google Compute Engine (Ubuntu 22.04 LTS, `e2-standard-2`, 2 vCPUs, 8 GB RAM, 30 GB SSD)  
**Project Workspace:** `F:\final project\HalluGuard`  
**Detector Submodule:** `F:\final project\LettuceDetect`

---

## 1. Executive Summary

Phase 5 Step 2 establishes the complete deployment configuration for deploying **HalluGuard** to a single Google Compute Engine (GCE) virtual machine. 

All deployment scripts, systemd service units, Nginx site configurations, production environment templates, and operational documentation were drafted and statically validated. The backend dependencies were updated to include `python-multipart`. No model weights, production thresholds, verification logic, or evaluation datasets were altered.

---

## 2. Manifest of Created & Modified Files

### 2.1 Files Created in `deployment/`

| File | Purpose | Key Parameters |
| :--- | :--- | :--- |
| [`deployment/setup_vm.sh`](file:///f:/final%20project/HalluGuard/deployment/setup_vm.sh) | Automated Ubuntu 22.04 VM provisioning script | Installs Python 3.11, Nginx, Node.js 20, venv, user `halluguard`, permissions |
| [`deployment/halluguard.service`](file:///f:/final%20project/HalluGuard/deployment/halluguard.service) | Systemd background daemon configuration | Uvicorn on `127.0.0.1:8000`, 1 worker, auto-restart, unprivileged user |
| [`deployment/nginx.conf`](file:///f:/final%20project/HalluGuard/deployment/nginx.conf) | Nginx reverse-proxy & static asset web server | Routes API to `127.0.0.1:8000`, serves `dist/`, 25MB body limit, 120s timeout |
| [`deployment/deploy_instructions.md`](file:///f:/final%20project/HalluGuard/deployment/deploy_instructions.md) | Step-by-step GCE operational deployment runbook | Full copy-paste commands from VM creation to SSL / Certbot setup |
| [`deployment/.env.production.example`](file:///f:/final%20project/HalluGuard/deployment/.env.production.example) | Secure production environment template | Production host/port, CPU mode, persistent HF cache, optional Supabase |

### 2.2 Files Modified

| File | Modification | Justification |
| :--- | :--- | :--- |
| [`backend/requirements.txt`](file:///f:/final%20project/HalluGuard/backend/requirements.txt) | Added `python-multipart>=0.0.18` under `# Core Framework` | Required by FastAPI `UploadFile` for `/documents/upload`. (Identified as missing in Step 1). |

---

## 3. Server Directory & Architecture Layout

On the target Google Compute Engine VM, the application structure is laid out under `/opt/halluguard` owned by the dedicated `halluguard:halluguard` system account:

```
/opt/halluguard/
├── HalluGuard/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py                     # FastAPI entry point
│   │   │   ├── config.py
│   │   │   ├── api/ (health, verification, documents)
│   │   │   └── services/ (detector, document, retrieval, supabase)
│   │   ├── .env                            # Mode 600 production environment file
│   │   └── requirements.txt
│   ├── frontend/
│   │   └── dist/                           # Compiled static SPA bundle (Nginx webroot)
│   └── deployment/
│       ├── setup_vm.sh
│       ├── halluguard.service
│       ├── nginx.conf
│       └── deploy_instructions.md
├── LettuceDetect/                          # Cloned LettuceDetect engine repository
│   └── lettucedetect/
├── cache/
│   └── huggingface/                        # Persistent HuggingFace model cache directory
└── venv/                                   # Isolated Python 3.11 virtual environment
```

---

## 4. Backend Installation & Runtime Setup

1. **Python 3.11 Runtime:** Ubuntu 22.04 LTS defaults to Python 3.10. `setup_vm.sh` installs Python 3.11 via the official `ppa:deadsnakes/ppa` repository along with `python3.11-venv` and `python3.11-dev`.
2. **Virtual Environment:** Initialized at `/opt/halluguard/venv`.
3. **Core Dependencies:** Installed via `/opt/halluguard/venv/bin/pip install -r /opt/halluguard/HalluGuard/backend/requirements.txt`.
4. **LettuceDetect Integration:** Because `LettuceDetect` is an editable package rather than an external PyPI package, `setup_vm.sh` installs it directly from the cloned repository:
   ```bash
   /opt/halluguard/venv/bin/pip install -e /opt/halluguard/LettuceDetect
   ```
5. **Execution Command:**
   ```bash
   /opt/halluguard/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
   ```
   *Single worker architecture is enforced* so that the ~1.5 GB ModernBERT model remains in RAM as a single resident process, preventing memory thrashing on the 8 GB VM.

---

## 5. Model Cache Preparation & Footprint

- **Cache Location:** `/opt/halluguard/cache/huggingface`
- **Environment Variable:** `HF_HOME=/opt/halluguard/cache/huggingface`
- **Cache Persistence:** The model weights (`model.safetensors`, 598.4 MB) are stored on the VM's 30 GB persistent disk. Once downloaded, subsequent service restarts or server reboots load directly from disk without network access.
- **Controlled Pre-Download Option:** To prevent uncontrolled downloads or service timeouts on first web request, `setup_vm.sh` supports a `--download-model` flag to pre-populate the cache during provisioning.

---

## 6. Systemd Daemon Configuration (`halluguard.service`)

The systemd configuration handles service lifecycle and process supervision:
- **Unit File:** `/etc/systemd/system/halluguard.service`
- **Execution User:** Dedicated unprivileged system user `halluguard`.
- **Security Sandboxing:**
  - `PrivateTmp=true`: Isolates `/tmp` directory.
  - `ProtectSystem=full`: Mounts `/usr`, `/boot`, and `/etc` read-only for the service process.
  - `ProtectHome=read-only`: Restricts home directory modifications.
- **Loopback Enforcement:** Binds strictly to `127.0.0.1:8000` (port 8000 is never exposed on the network).
- **Restart Policy:** `Restart=always` with `RestartSec=5s` automatically recovers the backend if terminated.

---

## 7. Nginx Reverse Proxy Architecture

Inspection confirmed that the FastAPI backend routes have **no global `/api` prefix**; endpoints are bare (e.g. `/health`, `/verify`, `/context/chunk`, `/documents/upload`).

Nginx is configured to handle both static hosting and API routing:
1. **Frontend Static Web Serving:**
   - Web root: `/opt/halluguard/HalluGuard/frontend/dist`
   - SPA Fallback: `try_files $uri $uri/ /index.html;` ensures React state navigation works without server 404s.
   - Static Asset Caching: `location /assets/` applies a 1-year immutable cache header for hashed JS/CSS assets.
2. **Backend Proxying:**
   - Regex route matching:
     ```nginx
     location ~ ^/(health|verify|context|verifications|documents|docs|redoc|openapi.json) {
         proxy_pass http://127.0.0.1:8000;
         proxy_http_version 1.1;
         proxy_set_header Host $host;
         proxy_set_header X-Real-IP $remote_addr;
         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
         proxy_set_header X-Forwarded-Proto $scheme;
         proxy_connect_timeout 60s;
         proxy_read_timeout 120s;
         proxy_send_timeout 120s;
         proxy_buffering off;
     }
     ```
3. **Upload Sizing:** `client_max_body_size 25M;` accommodates reference PDFs up to 25 MB.
4. **Security Filters:** Denies access to dotfiles (`.env`, `.git`) and source extensions (`.py`, `.sh`, `.log`).

---

## 8. Frontend Production Configuration & Build

- **Same-Origin API Routing:** In `frontend/src/services/api.ts`:
  ```typescript
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  ```
- **Production Build Command:**
  ```bash
  cd /opt/halluguard/HalluGuard/frontend
  VITE_API_BASE_URL="" npm run build
  ```
- **Why this works:** When `VITE_API_BASE_URL=""`, all frontend API calls become relative paths (e.g., `/verify`, `/health`). The client browser sends these requests directly to the origin host on port 80/443. Nginx intercepts them and proxies them to Uvicorn at `127.0.0.1:8000`. This completely eliminates cross-origin CORS issues and eliminates hardcoded IP addresses.

---

## 9. Security & Storage Persistence Assessment

### 9.1 Security Architecture
- **Principle of Least Privilege:** Daemon executes under `halluguard` user, not `root`.
- **Credential Protection:** `/opt/halluguard/HalluGuard/backend/.env` is set to `chmod 600` and `chown halluguard:halluguard`.
- **Network Surface:** Only TCP ports `80` (HTTP) and `443` (HTTPS) are exposed on the Google Cloud VPC firewall. SSH (port 22) is managed through Google Cloud IAP or authorized admin keys. Port `8000` is strictly internal.

### 9.2 Storage Persistence & Limitations
- **Current Baseline:** Reference documents (`_documents` dictionary) and verification history are stored in **process RAM**.
- **Behavior on Restart:** If the VM or Uvicorn restarts, session documents and in-memory history are cleared.
- **Persistent Database Option:** If long-term persistence is desired, connect Supabase PostgreSQL by setting `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `.env`. The database schema is pre-defined in `backend/app/database/schema.sql`.

---

## 10. Static Validation Results

A custom static inspection script was executed to verify all generated configuration files:

```text
Checking deployment files existence:
  [OK] setup_vm.sh (8,760 bytes)
  [OK] halluguard.service (1,042 bytes)
  [OK] nginx.conf (4,112 bytes)
  [OK] deploy_instructions.md (6,906 bytes)
  [OK] .env.production.example (1,400 bytes)
  [PASS] halluguard.service structure verified.
  [PASS] nginx.conf structure verified (6 balanced blocks).
  [PASS] All backend routes covered in Nginx proxy.
  [PASS] setup_vm.sh configuration and paths verified.
  [PASS] setup_vm.sh uses pure UNIX LF line endings.

ALL DEPLOYMENT ASSETS VALIDATED SUCCESSFULLY!
```

---

## 11. Exact VM Deployment Commands (Preview for Step 3)

When VM provisioning is approved, deployment on the target machine will execute via:

```bash
# 1. Clone repositories to /opt/halluguard
sudo mkdir -p /opt/halluguard && sudo chown -R $USER:$USER /opt/halluguard
cd /opt/halluguard
git clone <HALLUGUARD_REPO> HalluGuard
git clone https://github.com/KRLabsOrg/LettuceDetect.git LettuceDetect

# 2. Run automated VM provisioning
cd /opt/halluguard/HalluGuard/deployment
sudo bash setup_vm.sh --download-model

# 3. Configure production environment
sudo cp .env.production.example /opt/halluguard/HalluGuard/backend/.env
sudo chown halluguard:halluguard /opt/halluguard/HalluGuard/backend/.env
sudo chmod 600 /opt/halluguard/HalluGuard/backend/.env

# 4. Compile frontend
cd /opt/halluguard/HalluGuard/frontend
npm ci
VITE_API_BASE_URL="" npm run build

# 5. Start and verify service
sudo systemctl restart halluguard.service
sudo systemctl status halluguard.service
curl -s http://127.0.0.1:8000/health | jq .
```

---

## 12. Final Status & Next Steps

All deployment scripts and configurations are prepared and validated.

- No Google Cloud resources were created.
- No model weights or evaluation benchmarks were modified.
- The repository is fully prepared for Phase 5, Step 3 (Deployment Execution / Verification).

I will stop here and await your instruction before proceeding further.

