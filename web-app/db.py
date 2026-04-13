"""MongoDB access for outfit documents."""

import os
from pathlib import Path
from datetime import datetime

import pymongo
from bson import ObjectId
from dotenv import load_dotenv  # pylint: disable=import-error

load_dotenv(Path(__file__).resolve().parent / ".env")

client = pymongo.MongoClient(os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/"))
db = client["outfit_db"]
users_collection = db["users"]
outfits_collection = db["outfits"]

users_collection.create_index("username", unique=True)

def create_user(username, password_hash):
    user = {
        "username": username,
        "password_hash": password_hash,
        "created_at": datetime.now(),
        "last_login_at": None,
    }
    return users_collection.insert_one(user).inserted_id

def find_user_by_username(username):
    return users_collection.find_one({"username": username})

def find_user_by_id(user_id):
    return users_collection.find_one({"_id": ObjectId(user_id)})

def update_last_login(user_id):
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"last_login_at": datetime.now()}}
    )

def insert_outfit(doc):
    doc["created_at"] = datetime.now() #now db alwasys stores the time it's created. 
    """Insert one outfit document; return the new document's ObjectId."""
    return outfits_collection.insert_one(doc).inserted_id
