"""MongoDB access for outfit documents."""

import os
from pathlib import Path
from datetime import datetime

import pymongo
from bson import ObjectId
from dotenv import load_dotenv  # pylint: disable=import-error
from pymongo.errors import PyMongoError

_app_dir = Path(__file__).resolve().parent
_repo_dir = _app_dir.parent

load_dotenv(_app_dir / ".env")
load_dotenv(_repo_dir / ".env")

_mongo_uri = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/")
_db_name = os.environ.get("DB_NAME", "outfit_db")

client = pymongo.MongoClient(_mongo_uri)
db = client[_db_name]
users_collection = db["users"]
quotes_collection = db["quotes"]

_DEFAULT_QUOTES = [
    {
        "_id": ObjectId("69de7f3fd029128a5b5a7b43"),
        "tier": "high",
        "text": "Okayyyy fashion icon 💅 this combo is eating.",
        "is_active": True,
    },
    {
        "_id": ObjectId("69de7f3fd029128a5b5a7b44"),
        "tier": "high",
        "text": "Color harmony level: main character energy.",
        "is_active": True,
    },
    {
        "_id": ObjectId("69de7f3fd029128a5b5a7b45"),
        "tier": "high",
        "text": "This outfit? Approved by the fashion gods ✨",
        "is_active": True,
    },
    {
        "_id": ObjectId("69de7f3fd029128a5b5a7b46"),
        "tier": "medium",
        "text": "Hmm… it's giving 'almost there'.",
        "is_active": True,
    },
    {
        "_id": ObjectId("69de7f3fd029128a5b5a7b47"),
        "tier": "medium",
        "text": "Not bad, but your outfit is playing it a little safe.",
        "is_active": True,
    },
    {
        "_id": ObjectId("69de7f3fd029128a5b5a7b48"),
        "tier": "medium",
        "text": "We see the vision… but it needs a bit more spice 🌶️",
        "is_active": True,
    },
    {
        "_id": ObjectId("69de7f3fd029128a5b5a7b49"),
        "tier": "low",
        "text": "Respectfully… these colors are arguing 😭",
        "is_active": True,
    },
    {
        "_id": ObjectId("69de7f3fd029128a5b5a7b4a"),
        "tier": "low",
        "text": "This combo said 'let's not coordinate today'.",
        "is_active": True,
    },
    {
        "_id": ObjectId("69de7f3fd029128a5b5a7b4b"),
        "tier": "low",
        "text": "This combo is bold... maybe a little too bold.",
        "is_active": True,
    },
]


def _seed_quotes_if_empty():
    """Insert starter catalog rows so outfits can store real quote text and ids."""
    if quotes_collection.find_one() is not None:
        return
    quotes_collection.insert_many(_DEFAULT_QUOTES)


def init_db():
    """Initialize database indexes."""
    users_collection.create_index("username", unique=True)
    _seed_quotes_if_empty()


def create_user(username, password_hash):
    """Insert a new user document and return its ObjectId."""
    user = {
        "username": username,
        "password_hash": password_hash,
        "created_at": datetime.now(),
        "last_login_at": None,
        "outfits": [],
    }
    return users_collection.insert_one(user).inserted_id


def find_user_by_username(username):
    """Find a user by their username."""
    return users_collection.find_one({"username": username})


def find_user_by_id(user_id):
    """Find a user by their ObjectId."""
    return users_collection.find_one({"_id": ObjectId(user_id)})


def update_last_login(user_id):
    """Update the last login timestamp for a user."""
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"last_login_at": datetime.now()}},
    )


def insert_outfit(doc):
    """Append one outfit to the user's outfits array; return the new subdocument _id."""
    payload = dict(doc)
    user_id = payload.pop("user_id", None)
    if user_id is None:
        raise PyMongoError("outfit document missing user_id")

    outfit_id = ObjectId()
    payload["_id"] = outfit_id
    payload["created_at"] = datetime.now()

    result = users_collection.update_one(
        {"_id": user_id},
        {"$push": {"outfits": payload}},
    )
    if result.matched_count == 0:
        raise PyMongoError("user not found for outfit insert")

    return outfit_id


def get_all_outfits():
    """Return all outfit documents from all users."""
    all_outfits = []
    for user in users_collection.find():
        all_outfits.extend(user.get("outfits", []))
    return all_outfits


def get_outfits_by_user(user_id):
    """Return all outfits for a specific user."""
    if not user_id:
        return []
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return []
    if not user:
        return []
    return user.get("outfits", [])


def get_quote_by_tier(tier):
    """Return one random active quote for the given tier."""
    results = list(
        quotes_collection.aggregate(
            [
                {"$match": {"tier": tier, "is_active": True}},
                {"$sample": {"size": 1}},
            ]
        )
    )
    return results[0] if results else None
