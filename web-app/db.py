import os

import pymongo

client = pymongo.MongoClient(os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/"))
db = client["outfit_db"]
collection = db["outfits"]


def insert_outfit(doc):
    return collection.insert_one(doc).inserted_id