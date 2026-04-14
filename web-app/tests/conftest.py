"""Pytest fixtures for the Flask app."""

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["SKIP_DB_INIT"] = "1"

from app import app as flask_app  # noqa: E402


@pytest.fixture
def app():
    """Return the Flask app configured for testing."""
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
    )
    return flask_app


@pytest.fixture
def client(app):
    """Return a Flask test client."""
    return app.test_client()
