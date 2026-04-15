"""ML HTTP API: train on first /predict, then score hex pairs."""

import os

from flask import Flask, jsonify, request

from app.model import OutfitModel

app = Flask(__name__)
_model_holder = {}


def get_model():
    if "m" in _model_holder:
        return _model_holder["m"]
    if "train_error" in _model_holder:
        raise RuntimeError(_model_holder["train_error"])
    try:
        m = OutfitModel()
        m.train()
        _model_holder["m"] = m
        return m
    except Exception as exc:  # pylint: disable=broad-exception-caught
        msg = str(exc)
        _model_holder["train_error"] = msg
        raise RuntimeError(msg) from exc


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}
    top = (data.get("top") or "").strip()
    bottom = (data.get("bottom") or "").strip()
    if len(top) != 7 or len(bottom) != 7 or not top.startswith("#") or not bottom.startswith("#"):
        return jsonify({"ok": False, "error": "invalid_colors"}), 400
    try:
        model = get_model()
        score = model.predict_score(model.hex_to_rgb(top), model.hex_to_rgb(bottom))
    except (ValueError, RuntimeError) as exc:
        return jsonify({"ok": False, "error": str(exc)}), 503
    return jsonify({"ok": True, "score": score})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, threaded=True)
