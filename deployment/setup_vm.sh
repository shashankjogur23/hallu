#!/usr/bin/env bash
# ==============================================================================
# HalluGuard — Google Compute Engine VM Setup Script (Ubuntu 22.04 LTS)
# ==============================================================================
# This script provisions an Ubuntu 22.04 LTS VM (e2-standard-2) for HalluGuard:
#   1. Installs Python 3.11, Nginx, Node.js 20 LTS, and system build tools.
#   2. Creates the dedicated 'halluguard' service user.
#   3. Initializes directory structure under /opt/halluguard.
#   4. Sets up a dedicated Python 3.11 virtual environment.
#   5. Installs backend dependencies and LettuceDetect.
#   6. Configures Hugging Face persistent cache directory.
#   7. Installs systemd service and Nginx site configuration.
#
# Usage:
#   sudo bash setup_vm.sh [--download-model]
# ==============================================================================

set -euo pipefail

# Check for root privileges
if [[ $EUID -ne 0 ]]; then
   echo "[ERROR] This script must be run as root (use: sudo bash setup_vm.sh)"
   exit 1
fi

APP_USER="halluguard"
APP_DIR="/opt/halluguard"
BACKEND_DIR="${APP_DIR}/HalluGuard/backend"
FRONTEND_DIR="${APP_DIR}/HalluGuard/frontend"
LETTUCE_DIR="${APP_DIR}/LettuceDetect"
VENV_DIR="${APP_DIR}/venv"
CACHE_DIR="${APP_DIR}/cache/huggingface"
LOG_DIR="/var/log/halluguard"

DOWNLOAD_MODEL=false
if [[ "${1:-}" == "--download-model" ]]; then
    DOWNLOAD_MODEL=true
fi

echo "=============================================================================="
echo " HalluGuard Provisioning — Ubuntu 22.04 LTS"
echo "=============================================================================="

# ------------------------------------------------------------------------------
# 1. System Package Updates & Prerequisites
# ------------------------------------------------------------------------------
echo "[-] Step 1: Updating APT repositories..."
apt-get update -y
apt-get install -y --no-install-recommends \
    software-properties-common \
    ca-certificates \
    curl \
    git \
    build-essential \
    nginx \
    ufw

# ------------------------------------------------------------------------------
# 2. Python 3.11 Installation (via deadsnakes PPA for Ubuntu 22.04)
# ------------------------------------------------------------------------------
echo "[-] Step 2: Installing Python 3.11..."
if ! command -v python3.11 &>/dev/null; then
    add-apt-repository -y ppa:deadsnakes/ppa
    apt-get update -y
    apt-get install -y \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        python3-pip
fi

PYTHON_BIN=$(command -v python3.11)
echo "    Python binary: ${PYTHON_BIN} ($(${PYTHON_BIN} --version))"

# ------------------------------------------------------------------------------
# 3. Node.js 20 LTS Installation (for frontend production compilation)
# ------------------------------------------------------------------------------
echo "[-] Step 3: Installing Node.js 20 LTS..."
if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi
echo "    Node binary: $(command -v node) ($(node -v))"
echo "    NPM binary:  $(command -v npm)  (v$(npm -v))"

# ------------------------------------------------------------------------------
# 4. User and Directory Setup
# ------------------------------------------------------------------------------
echo "[-] Step 4: Configuring dedicated user and directories..."
if ! id -u "${APP_USER}" &>/dev/null; then
    useradd -m -s /bin/bash "${APP_USER}"
    echo "    Created system user '${APP_USER}'."
else
    echo "    User '${APP_USER}' already exists."
fi

mkdir -p "${APP_DIR}" "${CACHE_DIR}" "${LOG_DIR}"

# ------------------------------------------------------------------------------
# 5. Python Virtual Environment Setup
# ------------------------------------------------------------------------------
echo "[-] Step 5: Setting up Python 3.11 virtual environment..."
if [[ ! -d "${VENV_DIR}" ]]; then
    ${PYTHON_BIN} -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/pip" install --upgrade pip setuptools wheel

# ------------------------------------------------------------------------------
# 6. Dependency Installation
# ------------------------------------------------------------------------------
echo "[-] Step 6: Installing Python dependencies..."

if [[ -f "${BACKEND_DIR}/requirements.txt" ]]; then
    echo "    Installing backend dependencies from requirements.txt..."
    "${VENV_DIR}/bin/pip" install -r "${BACKEND_DIR}/requirements.txt"
else
    echo "    [WARN] ${BACKEND_DIR}/requirements.txt not found yet."
    echo "           Ensure repositories are placed in ${APP_DIR} before running backend."
fi

# Explicit safeguard for python-multipart
"${VENV_DIR}/bin/pip" install "python-multipart>=0.0.18"

# Install LettuceDetect package in editable mode
if [[ -d "${LETTUCE_DIR}" ]]; then
    echo "    Installing LettuceDetect from ${LETTUCE_DIR}..."
    "${VENV_DIR}/bin/pip" install -e "${LETTUCE_DIR}"
else
    echo "    [WARN] ${LETTUCE_DIR} directory not found yet."
    echo "           Remember to clone LettuceDetect to ${LETTUCE_DIR}."
fi

# ------------------------------------------------------------------------------
# 7. Model Cache Pre-population (Controlled / Optional)
# ------------------------------------------------------------------------------
if [[ "${DOWNLOAD_MODEL}" == "true" ]]; then
    echo "[-] Step 7: Pre-downloading LettuceDetect model into persistent cache..."
    export HF_HOME="${CACHE_DIR}"
    "${VENV_DIR}/bin/python" -c "
import os
from transformers import AutoModelForTokenClassification, AutoTokenizer
model_id = 'KRLabsOrg/lettucedect-base-modernbert-en-v1'
print(f'Downloading {model_id} to {os.environ.get(\"HF_HOME\")}...')
AutoTokenizer.from_pretrained(model_id)
AutoModelForTokenClassification.from_pretrained(model_id)
print('Model download complete.')
"
else
    echo "[-] Step 7: Skipping model pre-download (use --download-model flag if desired)."
    echo "           Model weights will download automatically during first service boot."
fi

# ------------------------------------------------------------------------------
# 8. Ownership and Permissions
# ------------------------------------------------------------------------------
echo "[-] Step 8: Applying secure file ownership and permissions..."
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}" "${LOG_DIR}"
chmod 750 "${APP_DIR}"
chmod 750 "${LOG_DIR}"

if [[ -f "${BACKEND_DIR}/.env" ]]; then
    chmod 600 "${BACKEND_DIR}/.env"
    chown "${APP_USER}:${APP_USER}" "${BACKEND_DIR}/.env"
fi

# ------------------------------------------------------------------------------
# 9. Systemd & Nginx Configuration Deployment
# ------------------------------------------------------------------------------
echo "[-] Step 9: Installing system configurations..."

# Copy systemd service if available
SERVICE_SRC="${APP_DIR}/HalluGuard/deployment/halluguard.service"
if [[ -f "${SERVICE_SRC}" ]]; then
    cp "${SERVICE_SRC}" /etc/systemd/system/halluguard.service
    systemctl daemon-reload
    systemctl enable halluguard.service
    echo "    Installed and enabled /etc/systemd/system/halluguard.service."
fi

# Copy Nginx config if available
NGINX_SRC="${APP_DIR}/HalluGuard/deployment/nginx.conf"
if [[ -f "${NGINX_SRC}" ]]; then
    cp "${NGINX_SRC}" /etc/nginx/sites-available/halluguard
    ln -sf /etc/nginx/sites-available/halluguard /etc/nginx/sites-enabled/halluguard
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
    echo "    Installed and enabled /etc/nginx/sites-enabled/halluguard."
fi

# ------------------------------------------------------------------------------
# 10. Firewall Configuration (UFW)
# ------------------------------------------------------------------------------
echo "[-] Step 10: Configuring local UFW firewall..."
ufw allow 22/tcp comment 'SSH' || true
ufw allow 80/tcp comment 'HTTP' || true
ufw allow 443/tcp comment 'HTTPS' || true
# Port 8000 remains strictly private to localhost!

echo "=============================================================================="
echo " HalluGuard Provisioning Complete!"
echo " Next steps:"
echo "   1. Ensure repositories are at ${APP_DIR}/HalluGuard and ${APP_DIR}/LettuceDetect."
echo "   2. Configure ${BACKEND_DIR}/.env with production settings."
echo "   3. Build the frontend: cd ${FRONTEND_DIR} && VITE_API_BASE_URL='' npm run build"
echo "   4. Start the service: sudo systemctl restart halluguard.service"
echo "   5. Check status:      sudo systemctl status halluguard.service"
echo "=============================================================================="

