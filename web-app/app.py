import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for
from pymongo.errors import PyMongoError
from werkzeug.exceptions import RequestEntityTooLarge

load_dotenv(Path(__file__).resolve().parent / ".env")

from db import insert_outfit

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


@app.errorhandler(RequestEntityTooLarge)
def _too_large(_e):
    return jsonify({"ok": False, "error": "payload_too_large"}), 413


@app.context_processor
def _ctx():
    # base.html shows nav when current_user.is_authenticated
    return {"current_user": SimpleNamespace(is_authenticated=True, id="guest")}


@app.route("/")
def index():
    return redirect(url_for("analyze"))


@app.route("/api/outfit", methods=["POST"])
def api_save_outfit():
    payload = request.get_json(silent=True) or {}
    top = (payload.get("top") or "").strip()
    bottom = (payload.get("bottom") or "").strip()
    photo_b64 = payload.get("photo")
    ts = payload.get("timestamp")
    if not top or not bottom or not photo_b64:
        return jsonify({"error": "top, bottom, and photo are required"}), 400
    if not top.startswith("#") or not bottom.startswith("#"):
        return jsonify({"error": "top and bottom must be #RRGGBB hex"}), 400

    score = 0
    if not ts:
        ts = datetime.now(timezone.utc).isoformat()

    doc = {
        "top": top,
        "bottom": bottom,
        "coordination_score": score,
        "timestamp": ts,
        "photo": photo_b64,
        "photo_mime": "image/jpeg",
    }
    try:
        oid = insert_outfit(doc)
    except PyMongoError as exc:
        return jsonify(
            {"ok": False, "error": "database_error", "detail": str(exc)}
        ), 503

    return jsonify(
        {
            "ok": True,
            "id": str(oid),
            "coordination_score": score,
            "top": top,
            "bottom": bottom,
            "timestamp": ts,
        }
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    return render_template("signup.html")


@app.route("/logout")
def logout():
    return redirect(url_for("login"))


@app.route("/analyze")
def analyze():
    return render_template("analyze.html")


@app.route("/stats")
def stats():
    return render_template("stats.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "3000")), debug=True)
