"""Pytest fixtures for HalluGuard backend test suite."""

import os
import sys
from pathlib import Path

# Enforce offline mode before importing transformers or huggingface
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.detector_service import detector_service
from app.services.hybrid_detector_service import hybrid_detector_service


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Session-scoped TestClient that initializes the application lifespan.

    Loads the real LettuceDetect and DeBERTa-v3 NLI models once for all integration tests.
    """
    with TestClient(app) as test_client:
        # Verify models loaded
        if not hybrid_detector_service.is_loaded:
            hybrid_detector_service.load_models()
        yield test_client

