"""
Seed script for inserting data into database
"""

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["outfit_db"]

data = [
    {"top_color": [255, 0, 0], "bottom_color": [0, 0, 0], "score": 0.9},
    {"top_color": [255, 0, 0], "bottom_color": [0, 255, 0], "score": 0.1},
    {"top_color": [0, 0, 255], "bottom_color": [255, 255, 255], "score": 0.8},
]

db.training_data.insert_many(data)
