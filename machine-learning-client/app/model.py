"""
Outfit matching ML model.

- Loads training data from MongoDB
- Trains a regression model to score outfit compatibility
- Predicts match score for new outfits
- Stores results back in MongoDB
"""

from typing import List, Tuple

import numpy as np
from pymongo import MongoClient
from sklearn.ensemble import RandomForestRegressor

import os


class OutfitModel:

    def __init__(self, training_collection=None, results_collection=None):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.trained = False

        if training_collection is None or results_collection is None:
            mongo_uri = os.getenv("MONGO_URI")
            db_name = os.getenv("DB_NAME", "outfit_db")

            if not mongo_uri:
                raise ValueError("MONGO_URI not set in environment")

            self.client = MongoClient(mongo_uri)
            self.db = self.client[db_name]

        self.training_collection = training_collection or self.db["training_data"]
        self.results_collection = results_collection or self.db["results"]

    def load_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load training data from MongoDB.

        Expected format:
        {
            "top_color": (#AAAAAA),
            "bottom_color": (#AAAAAA),
            "score": float 0 or 1
        }
        """
        data = list(self.training_collection.find())

        if not data:
            raise ValueError("No training data found in database")

        X: List[List[int]] = []
        y: List[float] = []

        for item in data:
            top = item["color1"]
            bottom = item["color2"]
            score = item["score"]

            top_rgb = self.hex_to_rgb(top)
            bottom_rgb = self.hex_to_rgb(bottom)

            X.append(top_rgb + bottom_rgb)  # [R,G,B,R,G,B]
            y.append(score)

        return np.array(X), np.array(y)

    def train(self) -> None:
        """
        Train the model.
        """
        X, y = self.load_training_data()

        self.model.fit(X, y)
        self.trained = True

    def predict_score(
        self,
        top_color: Tuple[int, int, int],
        bottom_color: Tuple[int, int, int],
    ) -> float:
        """
        Predict match score between 0 and 1.
        """
        if not self.trained:
            raise RuntimeError("Model must be trained before prediction")

        features = np.array([list(top_color) + list(bottom_color)])

        score = self.model.predict(features)[0]

        # Clamp between 0 and 1
        score = max(0.0, min(1.0, float(score)))

        return score

    def save_result(
        self,
        top_color: Tuple[int, int, int],
        bottom_color: Tuple[int, int, int],
        score: float,
    ) -> None:
        self.results_collection.insert_one(
            {
                "color1": self.rgb_to_hex(top_color),
                "color2": self.rgb_to_hex(bottom_color),
                "match": score,
            }
        )

    def evaluate_outfit(self, top_hex: str, bottom_hex: str) -> float:
        """
        Predict and store result.
        """
        top_rgb = self.hex_to_rgb(top_hex)
        bottom_rgb = self.hex_to_rgb(bottom_hex)

        score = self.predict_score(top_rgb, bottom_rgb)
        self.save_result(top_rgb, bottom_rgb, score)

        return score

    def hex_to_rgb(self, hex_color: str) -> List[int]:
        """
        Convert hex color (#AAAAAA) to [R, G, B]
        """
        hex_color = hex_color.lstrip("#")

        return [
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        ]

    def rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """
        Convert [R, G, B] → "#RRGGBB"
        """
        return "#{:02X}{:02X}{:02X}".format(*rgb)
