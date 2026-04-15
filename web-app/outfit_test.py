"""Tests for POST /api/outfit (webcam JSON save)."""

# pylint: disable=wrong-import-position,wrong-import-order

import os

os.environ["MONGO_URI"] = "mongodb://127.0.0.1:27017/"
os.environ["SKIP_DB_INIT"] = "1"

import mongomock
import pymongo

pymongo.MongoClient = mongomock.MongoClient

from unittest.mock import patch

import pytest
from bson import ObjectId
from pymongo.errors import PyMongoError

from app import app as fitcheck_app


@pytest.fixture(name="client")
def flask_client():
    """Flask test client with testing config."""
    fitcheck_app.config["TESTING"] = True
    with fitcheck_app.test_client() as client:
        yield client


def _login(client):
    """Set a fake logged-in session for protected routes."""
    with client.session_transaction() as sess:
        sess["user_id"] = "test-user-id"
        sess["username"] = "sara123"


def _valid_payload():
    return {
        "top": "#ff0000",
        "bottom": "#00ff00",
        "photo": "/9j/4AAQSkZJRg==",
        "timestamp": "2026-01-01T12:00:00+00:00",
    }


@patch("app.get_quote_by_tier")
@patch("app.insert_outfit")
def test_api_save_outfit_persists_json(mock_insert, mock_get_quote, client):
    """POST /api/outfit saves the webcam JSON payload and returns ok + id."""
    _login(client)

    oid = ObjectId()
    mock_insert.return_value = oid
    mock_get_quote.return_value = {
        "tier": "high",
        "text": "Okayyyy fashion icon 💅 this combo is eating.",
        "is_active": True,
    }
    payload = _valid_payload()

    rv = client.post("/api/outfit", json=payload)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["ok"] is True
    assert data["id"] == str(oid)
    assert data["top"] == payload["top"]
    assert data["bottom"] == payload["bottom"]
    assert data["timestamp"] == payload["timestamp"]
    assert data["coordination_score"] == 0

    mock_insert.assert_called_once()
    saved = mock_insert.call_args[0][0]
    assert saved["top"] == payload["top"]
    assert saved["bottom"] == payload["bottom"]
    assert saved["photo"] == payload["photo"]
    assert saved["timestamp"] == payload["timestamp"]
    assert saved["photo_mime"] == "image/jpeg"


@patch("app.insert_outfit")
def test_api_save_outfit_missing_photo_rejected(mock_insert, client):
    """Missing photo (webcam capture) yields 400 and no DB write."""
    _login(client)

    rv = client.post(
        "/api/outfit",
        json={"top": "#111111", "bottom": "#222222"},
    )
    assert rv.status_code == 400
    assert "required" in (rv.get_json() or {}).get("error", "")
    mock_insert.assert_not_called()


@patch("app.insert_outfit")
def test_api_save_outfit_invalid_hex_rejected(mock_insert, client):
    """Non-hex color strings yield 400."""
    _login(client)

    payload = _valid_payload()
    payload["top"] = "red"
    rv = client.post("/api/outfit", json=payload)
    assert rv.status_code == 400
    mock_insert.assert_not_called()


@patch("app.get_quote_by_tier")
@patch("app.insert_outfit")
def test_api_save_outfit_database_error(mock_insert, mock_get_quote, client):
    """Mongo errors surface as 503 with ok False."""
    _login(client)

    mock_get_quote.return_value = {
        "tier": "high",
        "text": "Okayyyy fashion icon 💅 this combo is eating.",
        "is_active": True,
    }
    mock_insert.side_effect = PyMongoError("connection refused")
    rv = client.post("/api/outfit", json=_valid_payload())
    assert rv.status_code == 503
    data = rv.get_json()
    assert data["ok"] is False
    assert data["error"] == "database_error"
