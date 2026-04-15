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


_TEST_USER_ID = "507f1f77bcf86cd799439011"


def _login(client):
    """Set a fake logged-in session for protected routes."""
    with client.session_transaction() as sess:
        sess["user_id"] = _TEST_USER_ID
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
    qid = ObjectId()
    mock_insert.return_value = oid
    mock_get_quote.return_value = {
        "_id": qid,
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
    assert saved["tier"] == "low"
    assert saved["coordination_score"] == 0
    assert saved["quote"] == mock_get_quote.return_value["text"]
    assert saved["quote_id"] == str(qid)
    assert saved["user_id"] == ObjectId(_TEST_USER_ID)
    assert data["quote"] == mock_get_quote.return_value["text"]
    assert data["quote_id"] == str(qid)
    assert data["user_id"] == _TEST_USER_ID


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


def test_delete_outfit_requires_login(client):
    """Delete endpoint should require login."""
    rv = client.post(f"/outfits/{ObjectId()}/delete", follow_redirects=False)
    assert rv.status_code == 302
    assert "/login" in rv.headers["Location"]


@patch("app.delete_outfit_for_user", return_value=True)
def test_delete_outfit_success(mock_delete, client):
    """Delete endpoint calls helper and redirects."""
    _login(client)
    oid = str(ObjectId())
    rv = client.post(f"/outfits/{oid}/delete", follow_redirects=False)
    assert rv.status_code == 302
    assert "/outfits" in rv.headers["Location"]
    mock_delete.assert_called_once_with(_TEST_USER_ID, oid)
