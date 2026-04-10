from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["outfit_db"]
collection = db["results"]

def insert_result(data):
    collection.insert_one(data)

def get_latest():
    return collection.find_one(sort=[("_id", -1)])
