"""
Database module for MongoDB operations.
"""

import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["outfit_db"]
collection = db["results"]


def insert_result(data):
    """Insert a document into MongoDB."""
    collection.insert_one(data)


def get_latest():
    """Retrieve the latest document from MongoDB."""
    return collection.find_one(sort=[("_id", -1)])
