"""MongoDB access for outfit documents."""

import os
from pathlib import Path
from datetime import datetime

import pymongo
from bson import ObjectId
from dotenv import load_dotenv  # pylint: disable=import-error

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

client = pymongo.MongoClient(os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/"))
db = client["outfit_db"]
users_collection = db["users"]
outfits_collection = db["outfits"]
quotes_collection = db["quotes"]


def init_db():
    """Initialize database indexes."""
    users_collection.create_index("username", unique=True)


def create_user(username, password_hash):
    """Insert a new user document and return its ObjectId."""
    user = {
        "username": username,
        "password_hash": password_hash,
        "created_at": datetime.now(),
        "last_login_at": None,
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
    """Insert one outfit document; return the new document's ObjectId."""
    doc["created_at"] = datetime.now()  # Store database insertion time.
    return outfits_collection.insert_one(doc).inserted_id


def get_all_outfits():
    """Return all outfit documents."""
    return list(outfits_collection.find())


def get_outfits_by_user(user_id):
    """Return all outfits for a specific user."""
    return list(outfits_collection.find({"user_id": user_id}))


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
