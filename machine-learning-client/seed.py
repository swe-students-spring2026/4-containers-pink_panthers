"""
Seed script for inserting testing data into database based on general fashion rules
"""

import os
import random
import colorsys
from pymongo import MongoClient
from dotenv import load_dotenv

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = "training_data"

# -----------------------------
# MongoDB Connection
# -----------------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


# -----------------------------
# Helpers
# -----------------------------
def rgb_to_hex(rgb):
    """Convert RGB tuple to HEX string."""
    r, g, b = rgb
    return f"#{r:02X}{g:02X}{b:02X}"


def random_color():
    """Generate a random RGB color."""
    return (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    )


def get_hsv(rgb):
    """Convert RGB to HSV color space."""
    r, g, b = [x / 255.0 for x in rgb]
    return colorsys.rgb_to_hsv(r, g, b)


def hue_distance(h1, h2):
    """Calculate circular distance between two hues."""
    diff = abs(h1 - h2)
    return min(diff, 1 - diff)


# -----------------------------
# Neutral palette
# -----------------------------
NEUTRALS = [
    (0, 0, 0),
    (255, 255, 255),
    (128, 128, 128),
    (245, 245, 220),
]


# -----------------------------
# Matching logic
# -----------------------------
def is_good_match(c1, c2):
    """Determine if two colors match based on heuristic rules."""
    h1, _, v1 = get_hsv(c1)
    h2, _, v2 = get_hsv(c2)

    if c1 in NEUTRALS or c2 in NEUTRALS:
        return True

    if hue_distance(h1, h2) > 0.45:
        return True

    if hue_distance(h1, h2) < 0.15 and abs(v1 - v2) > 0.25:
        return True

    return False


# -----------------------------
# Generate dataset
# -----------------------------
def generate_pairs(n=2000):
    """Generate labeled outfit color pairs."""
    pairs = []

    for _ in range(n):
        c1 = random_color()
        c2 = random_color()

        score = 1 if is_good_match(c1, c2) else 0

        pairs.append(
            {
                "color1": rgb_to_hex(c1),
                "color2": rgb_to_hex(c2),
                "score": score,
            }
        )

    return pairs


# -----------------------------
# Insert into MongoDB
# -----------------------------
def insert_data(data):
    """Insert generated data into MongoDB."""
    if not data:
        return

    collection.insert_many(data)
    print(f"Inserted {len(data)} records into {DB_NAME}.training_data")


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    output = generate_pairs()
    insert_data(output)
