# Test MongoDB connection and insertion
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["outfit_db"]
collection = db["results"]

collection.insert_one({"test": "works"})

print("Inserted!")