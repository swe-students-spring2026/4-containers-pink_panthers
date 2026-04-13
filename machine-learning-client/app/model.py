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


class OutfitModel:

    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/") -> None:
        self.client = MongoClient(mongo_uri)
        self.db = self.client["outfit_db"]

        self.training_collection = self.db["training_data"]
        self.results_collection = self.db["results"]

        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.trained = False

    def load_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load training data from MongoDB.

        Expected format:
        {
            "top_color": [R, G, B],
            "bottom_color": [R, G, B],
            "score": float (0.0 - 1.0)
        }
        """
        data = list(self.training_collection.find())

        if not data:
            raise ValueError("No training data found in database")

        X: List[List[int]] = []
        y: List[float] = []

        for item in data:
            top = item["top_color"]
            bottom = item["bottom_color"]
            score = item["score"]

            X.append(top + bottom)  # [R,G,B,R,G,B]
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
        """
        Save result to MongoDB.
        """
        self.results_collection.insert_one(
            {
                "top_color": list(top_color),
                "bottom_color": list(bottom_color),
                "score": score,
            }
        )

    def evaluate_outfit(
        self,
        top_color: Tuple[int, int, int],
        bottom_color: Tuple[int, int, int],
    ) -> float:
        """
        Predict and store result.
        """
        score = self.predict_score(top_color, bottom_color)

        self.save_result(top_color, bottom_color, score)

        return score
