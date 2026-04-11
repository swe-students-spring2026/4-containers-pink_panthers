"""
Database helper for the web app.
"""

import os
import pymongo

client = pymongo.MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/"))
db = client["outfit_db"]
collection = db["results"]


def get_latest():
    """Return the most recent MongoDB document."""
    return collection.find_one(sort=[("_id", -1)])
