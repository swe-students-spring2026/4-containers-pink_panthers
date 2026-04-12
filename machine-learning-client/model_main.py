from model import OutfitModel

model = OutfitModel()

# Train model from DB
model.train()

# Example input
top = (215, 55, 74)      # red-ish
bottom = (60, 68, 78)    # dark gray

score = model.evaluate_outfit(top, bottom)

print(f"Match score: {score:.2f}")