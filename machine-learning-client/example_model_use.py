"""
Example script for OutfitModel

- Connects via MONGO_URI + DB_NAME
- Trains model on MONGODB training data
- Runs outfit prediction
- Saves result to MongoDB results collection
"""

from dotenv import load_dotenv
from app.model import OutfitModel

load_dotenv()


def main():
    """Test model with example color pair."""

    top_color = "#1325C8"
    bottom_color = "#000000"

    print("Starting OutfitModel test...")

    model = OutfitModel()

    print("Training model...")
    model.train()
    print("Model trained successfully.")

    print(f"Testing outfit: top={top_color}, bottom={bottom_color}")

    score = model.evaluate_outfit(top_color, bottom_color)

    print(f"Predicted match score: {score:.4f}")
    print("Result saved to MongoDB.")


if __name__ == "__main__":
    main()
