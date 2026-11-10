# HalluGuard — Google Compute Engine Deployment Guide

**Target Environment:** Google Compute Engine (GCE)  
**Machine Type:** `e2-standard-2` (2 vCPUs, 8 GB RAM, 30 GB persistent disk)  
**Operating System:** Ubuntu 22.04 LTS x86_64  
**Serving Topology:** Nginx Reverse Proxy (Ports 80/443) + FastAPI/Uvicorn (127.0.0.1:8000)

---

## 1. Overview of Deployment Architecture

```
Internet (Browser) ──► Port 80/443 ──► Nginx Web Server
                                         ├── /          ──► /opt/halluguard/HalluGuard/frontend/dist (Static SPA)
                                         └── /verify    ──► 127.0.0.1:8000 (Uvicorn / FastAPI Backend)
                                             /health        └── LettuceDetect ModernBERT (Resident in RAM)
                                             /documents
```

---

## 2. Google Cloud VM Provisioning

### Step 2.1: Create Compute Engine VM Instance
Using the Google Cloud Console or `gcloud` CLI:

- **Instance Name:** `halluguard-prod`
- **Region / Zone:** `us-central1-a` (or your preferred region)
- **Machine Configuration:**
  - Series: `E2`
  - Machine Type: `e2-standard-2` (2 vCPU, 8 GB memory)
- **Boot Disk:**
  - OS: `Ubuntu`
  - Version: `Ubuntu 22.04 LTS (x86/64)`
  - Size: `30 GB` (Standard persistent disk or Balanced persistent disk)
- **Firewall:**
  - [x] Allow HTTP traffic (port 80)
  - [x] Allow HTTPS traffic (port 443)

### Step 2.2: Verify VPC Firewall Rules
Ensure the Google Cloud VPC firewall has rules for target tags:
- `default-allow-http`: TCP port 80 from `0.0.0.0/0`
- `default-allow-https`: TCP port 443 from `0.0.0.0/0`
- `default-allow-ssh`: TCP port 22 (restricted to authorized IP or IAP)
- **Note:** Port 8000 must **NOT** be opened to the public internet.

---

## 3. Server Setup and Code Transfer

### Step 3.1: Connect via SSH
```bash
gcloud compute ssh halluguard-prod --zone=us-central1-a
```
Or connect via the browser SSH button in the Google Cloud Console.

### Step 3.2: Prepare Application Directory
```bash
sudo mkdir -p /opt/halluguard
sudo chown -R $USER:$USER /opt/halluguard
```

### Step 3.3: Clone or Copy Repositories
Clone both the main application and the detector repository into `/opt/halluguard`:
```bash
cd /opt/halluguard

# 1. Main Application
git clone <YOUR_HALLUGUARD_GIT_URL> HalluGuard

# 2. Detector Engine Repository
git clone https://github.com/KRLabsOrg/LettuceDetect.git LettuceDetect
```
*(If transferring from a local archive without Git, ensure `/opt/halluguard/HalluGuard` and `/opt/halluguard/LettuceDetect` exist as parallel directories).*

---

## 4. Run Automated Provisioning

Execute the automated provisioning script with root privileges:
```bash
cd /opt/halluguard/HalluGuard/deployment
sudo bash setup_vm.sh --download-model
```

The script will automatically:
1. Update apt repositories and install Python 3.11, Nginx, Node.js 20 LTS, and build tools.
2. Create the system user `halluguard`.
3. Create the Python 3.11 virtual environment at `/opt/halluguard/venv`.
4. Install all backend dependencies, `python-multipart`, and `LettuceDetect`.
5. Pre-download `KRLabsOrg/lettucedect-base-modernbert-en-v1` into `/opt/halluguard/cache/huggingface`.
6. Configure the systemd service `/etc/systemd/system/halluguard.service`.
7. Configure the Nginx reverse proxy at `/etc/nginx/sites-enabled/halluguard`.
8. Configure local firewall (UFW) rules.

---

## 5. Configure Production Environment

Create the production `.env` file from the provided template:
```bash
sudo cp /opt/halluguard/HalluGuard/deployment/.env.production.example /opt/halluguard/HalluGuard/backend/.env
```

Review or edit settings:
```bash
sudo nano /opt/halluguard/HalluGuard/backend/.env
```
Ensure:
- `APP_HOST=127.0.0.1`
- `APP_PORT=8000`
- `DEVICE=cpu`
- `HF_HOME=/opt/halluguard/cache/huggingface`

Lock down file permissions so only the `halluguard` service user can read it:
```bash
sudo chown halluguard:halluguard /opt/halluguard/HalluGuard/backend/.env
sudo chmod 600 /opt/halluguard/HalluGuard/backend/.env
```

---

## 6. Build Frontend for Production

Compile the React frontend with same-origin relative API pathing:
```bash
cd /opt/halluguard/HalluGuard/frontend

# Install dependencies
npm ci

# Build with empty API base URL so client requests are routed through Nginx
VITE_API_BASE_URL="" npm run build
```
Verify the build output:
```bash
ls -la /opt/halluguard/HalluGuard/frontend/dist/
```
Output must contain `index.html` and the `assets/` directory.

---

## 7. Start and Verify Services

### Step 7.1: Start the Backend Service
```bash
sudo systemctl daemon-reload
sudo systemctl restart halluguard.service
```

### Step 7.2: Monitor Startup Logs
Check systemd logs to verify model initialization:
```bash
journalctl -u halluguard.service -f
```
Expected output:
```text
Loading LettuceDetect model on CPU...
LettuceDetect model loaded successfully in 45.20 seconds.
LettuceDetect model ready for inference.
Application startup complete. Uvicorn running on http://127.0.0.1:8000
```

### Step 7.3: Test Health Endpoint (Local Loopback)
```bash
curl -s http://127.0.0.1:8000/health | jq .
```
Expected JSON:
```json
{
  "status": "healthy",
  "detector_loaded": true,
  "model_name": "KRLabsOrg/lettucedect-base-modernbert-en-v1",
  "device": "cpu",
  "supabase_configured": false,
  "version": "1.0.0"
}
```

### Step 7.4: Test Nginx Routing
```bash
curl -I http://127.0.0.1/
curl -s http://127.0.0.1/health | jq .
```

---

## 8. Domain and SSL/TLS Configuration (HTTPS)

Once your domain's DNS A-record points to the VM's external IP address:

### Step 8.1: Install Certbot
```bash
sudo apt-get install -y certbot python3-certbot-nginx
```

### Step 8.2: Obtain and Configure Let's Encrypt Certificate
```bash
sudo certbot --nginx -d yourdomain.com
```
Follow the interactive prompts to configure automatic HTTP-to-HTTPS redirect.

---

## 9. Security & Storage Persistence Considerations

1. **Service User Isolation:** The backend runs under the unprivileged `halluguard` system account.
2. **Loopback Binding:** Port 8000 is bound strictly to `127.0.0.1`, completely inaccessible from external networks.
3. **Storage Persistence:**
   - Uploaded PDF/TXT documents and verification history are stored in **session RAM** by default.
   - If the VM restarts or Uvicorn restarts, session documents are cleared.
   - For permanent persistence, connect Supabase PostgreSQL by populating `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `/opt/halluguard/HalluGuard/backend/.env`.

---

## 10. Operational Runbook

### Service Management Commands:
- **Restart backend:** `sudo systemctl restart halluguard.service`
- **View live logs:** `journalctl -u halluguard.service -f`
- **Check service status:** `sudo systemctl status halluguard.service`
- **Reload Nginx config:** `sudo nginx -t && sudo systemctl reload nginx`

