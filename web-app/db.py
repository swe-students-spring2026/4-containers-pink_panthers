"""MongoDB access for outfit documents."""

import os
from pathlib import Path

import pymongo
from dotenv import load_dotenv  # pylint: disable=import-error

load_dotenv(Path(__file__).resolve().parent / ".env")

client = pymongo.MongoClient(os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/"))
db = client["outfit_db"]
collection = db["outfits"]


def insert_outfit(doc):
    """Insert one outfit document; return the new document's ObjectId."""
    return collection.insert_one(doc).inserted_id
