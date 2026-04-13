import pytest
from app.model import OutfitModel
from tests.fake_collection import FakeCollection


def test_prediction_runs():
    fake_training = FakeCollection()

    model = OutfitModel(training_collection=fake_training)

    model.model.fit([[255, 0, 0, 0, 0, 0]], [1.0])
    model.trained = True

    score = model.predict_score((255, 0, 0), (0, 0, 0))

    assert 0.0 <= score <= 1.0


def test_model_requires_training():
    fake_training = FakeCollection()

    model = OutfitModel(training_collection=fake_training)

    with pytest.raises(RuntimeError):
        model.predict_score((255, 0, 0), (0, 0, 0))


def test_load_training_data():
    fake_training = FakeCollection()

    model = OutfitModel(training_collection=fake_training)

    # mock collection directly
    model.training_collection.insert_one(
        {"top_color": [255, 0, 0], "bottom_color": [0, 0, 0], "score": 1.0}
    )

    X, y = model.load_training_data()

    assert len(X) > 0
    assert len(y) > 0


def test_evaluate_outfit():
    fake_training = FakeCollection()
    fake_results = FakeCollection()

    model = OutfitModel(training_collection=fake_training,
                        results_collection=fake_results)

    model.model.fit([[255, 0, 0, 0, 0, 0]], [1.0])
    model.trained = True

    score = model.evaluate_outfit((255, 0, 0), (0, 0, 0))

    assert 0.0 <= score <= 1.0


def test_train_runs():
    fake_training = FakeCollection()

    model = OutfitModel(training_collection=fake_training)

    model.training_collection.insert_one(
        {"top_color": [255, 0, 0], "bottom_color": [0, 0, 0], "score": 1.0}
    )

    model.train()

    assert model.trained is True


def test_empty_database_raises_error():
    fake_training = FakeCollection()

    model = OutfitModel(training_collection=fake_training)

    # Make sure DB is empty OR point to a fake collection
    model.training_collection.delete_many({})

    with pytest.raises(ValueError, match="No training data found"):
        model.load_training_data()
