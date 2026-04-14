"""FitCheck Flask application."""

import os
from datetime import datetime, timezone

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from pymongo.errors import PyMongoError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.security import generate_password_hash, check_password_hash

from db import (
    create_user,
    find_user_by_username,
    init_db,
    insert_outfit,
    update_last_login,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

if os.environ.get("SKIP_DB_INIT") != "1":
    init_db()


@app.errorhandler(RequestEntityTooLarge)
def _too_large(_e):
    """Return JSON when request body exceeds MAX_CONTENT_LENGTH."""
    return jsonify({"ok": False, "error": "payload_too_large"}), 413


@app.context_processor
def _ctx():
    """Expose current user info from session for templates."""
    user_id = session.get("user_id")
    username = session.get("username")
    return {
        "current_user": {
            "is_authenticated": bool(user_id),
            "id": user_id,
            "username": username,
        }
    }


@app.route("/")
def index():
    """Redirect home to the analyze page."""
    return redirect(url_for("analyze"))


@app.route("/api/outfit", methods=["POST"])
def api_save_outfit():
    """Accept JSON outfit payload and persist it to MongoDB."""
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
        return (
            jsonify({"ok": False, "error": "database_error", "detail": str(exc)}),
            503,
        )

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
    """Render login page on GET and authenticate on POST."""
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    user = find_user_by_username(username)
    if not user:
        return render_template(
            "login.html",
            error="Invalid username or password.",
        )

    if not check_password_hash(user["password_hash"], password):
        return render_template(
            "login.html",
            error="Invalid username or password.",
        )

    session["user_id"] = str(user["_id"])
    session["username"] = user["username"]
    update_last_login(user["_id"])

    flash("Logged in successfully.", "success")
    return redirect(url_for("analyze"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Render the signup page."""
    if request.method == "GET":
        return render_template("signup.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    # Basic validation
    if len(username) < 3:
        return render_template(
            "signup.html",
            error="Username must be at least 3 characters long.",
        )

    if len(password) < 8:
        return render_template(
            "signup.html",
            error="Password must be at least 8 characters long.",
        )

    if password != confirm_password:
        return render_template(
            "signup.html",
            error="Passwords do not match.",
        )

    existing_user = find_user_by_username(username)
    if existing_user:
        return render_template(
            "signup.html",
            error="Username already exists.",
        )

    password_hash = generate_password_hash(password)
    create_user(username, password_hash)

    flash("Account created successfully. Please log in.", "success")
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    """Clear the session and redirect to the login page."""
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/analyze")
def analyze():
    """Render the webcam / outfit capture page."""
    return render_template("analyze.html")


@app.route("/stats")
def stats():
    """Render the stats page."""
    return render_template("stats.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "3000")), debug=True)
