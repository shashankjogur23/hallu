# HalluGuard Backend Package
import os

# Ensure huggingface and transformers run in offline mode to prevent network timeouts on local models
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
