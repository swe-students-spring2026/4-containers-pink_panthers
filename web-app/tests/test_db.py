"""Unit tests for db.py helper functions."""

from unittest.mock import MagicMock, patch

from bson import ObjectId

import db


@patch("db.quotes_collection")
@patch("db.users_collection")
def test_init_db_creates_username_index(mock_users_collection, mock_quotes_collection):
    """Test that init_db creates a unique index on the username field."""
    mock_quotes_collection.find_one.return_value = {"_id": "exists"}
    db.init_db()
    mock_users_collection.create_index.assert_called_once_with("username", unique=True)
    mock_quotes_collection.insert_many.assert_not_called()


@patch("db.quotes_collection")
@patch("db.users_collection")
def test_init_db_seeds_quotes_when_catalog_empty(
    mock_users_collection, mock_quotes_collection
):
    """Test that init_db inserts default quotes when the quotes collection is empty."""
    mock_quotes_collection.find_one.return_value = None
    db.init_db()
    mock_quotes_collection.insert_many.assert_called_once()
    batch = mock_quotes_collection.insert_many.call_args[0][0]
    assert len(batch) == 9
    assert {q["tier"] for q in batch} == {"low", "medium", "high"}


@patch("db.users_collection")
def test_create_user_inserts_document(mock_users_collection):
    """Test that create_user inserts a user document with the correct fields."""
    fake_id = ObjectId()
    mock_users_collection.insert_one.return_value.inserted_id = fake_id

    result = db.create_user("sara", "hashed-password")

    assert result == fake_id
    inserted_doc = mock_users_collection.insert_one.call_args[0][0]
    assert inserted_doc["username"] == "sara"
    assert inserted_doc["password_hash"] == "hashed-password"
    assert inserted_doc["last_login_at"] is None
    assert inserted_doc["outfits"] == []
    assert "created_at" in inserted_doc


@patch("db.users_collection")
def test_find_user_by_username_calls_find_one(mock_users_collection):
    """Test that find_user_by_username calls find_one with the correct query."""
    db.find_user_by_username("sara")
    mock_users_collection.find_one.assert_called_once_with({"username": "sara"})


@patch("db.users_collection")
def test_find_user_by_id_calls_find_one_with_objectid(mock_users_collection):
    """Test that find_user_by_id calls find_one with the correct query."""
    user_id = "507f1f77bcf86cd799439011"

    db.find_user_by_id(user_id)

    mock_users_collection.find_one.assert_called_once_with({"_id": ObjectId(user_id)})


@patch("db.users_collection")
def test_update_last_login_calls_update_one(mock_users_collection):
    """Test that update_last_login calls update_one with the correct query and update."""
    user_id = "507f1f77bcf86cd799439011"

    db.update_last_login(user_id)

    args = mock_users_collection.update_one.call_args[0]
    assert args[0] == {"_id": ObjectId(user_id)}
    assert "$set" in args[1]
    assert "last_login_at" in args[1]["$set"]


@patch("db.users_collection")
def test_insert_outfit_pushes_to_user_outfits(mock_users_collection):
    """Test that insert_outfit appends an outfit to users.outfits via $push with _id and created_at."""
    mock_users_collection.update_one.return_value = MagicMock(matched_count=1)
    uid = ObjectId()

    doc = {
        "user_id": uid,
        "top": "#ffffff",
        "bottom": "#000000",
        "photo": "dummy",
    }

    result = db.insert_outfit(doc)

    assert isinstance(result, ObjectId)
    mock_users_collection.update_one.assert_called_once()
    query, update = mock_users_collection.update_one.call_args[0]
    assert query == {"_id": uid}
    assert "$push" in update
    pushed = update["$push"]["outfits"]
    assert pushed["top"] == "#ffffff"
    assert pushed["bottom"] == "#000000"
    assert pushed["photo"] == "dummy"
    assert pushed["_id"] == result
    assert "user_id" not in pushed
    assert "created_at" in pushed


@patch("db.quotes_collection")
def test_get_quote_by_tier_returns_random_quote_when_found(mock_quotes_collection):
    """Test that get_quote_by_tier returns a random active quote for the given tier."""
    mock_quotes_collection.aggregate.return_value = [
        {"tier": "high", "text": "slay", "is_active": True}
    ]

    result = db.get_quote_by_tier("high")

    assert result == {"tier": "high", "text": "slay", "is_active": True}
    mock_quotes_collection.aggregate.assert_called_once()


@patch("db.quotes_collection")
def test_get_quote_by_tier_returns_none_when_no_quotes(mock_quotes_collection):
    """Test that get_quote_by_tier returns None if no active quotes are found for the tier."""
    mock_quotes_collection.aggregate.return_value = []

    result = db.get_quote_by_tier("low")

    assert result is None
    mock_quotes_collection.aggregate.assert_called_once()
