"""FitCheck Flask application."""

import json
import os
import urllib.error
import urllib.request
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
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import PyMongoError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.security import generate_password_hash, check_password_hash

from db import (
    create_user,
    delete_outfit_for_user,
    find_user_by_username,
    get_all_outfits,
    get_outfits_by_user,
    get_quote_by_tier,
    init_db,
    insert_outfit,
    update_last_login,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

if os.environ.get("SKIP_DB_INIT", "1") != "1":
    init_db()


def score_to_tier(score):
    """Convert a numeric coordination score into a quote tier."""
    if score >= 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def fetch_coordination_score(top_hex: str, bottom_hex: str) -> float:
    """Return ML coordination score for two hex colors, or 0.0 when ML_BASE_URL is unset."""
    base = (os.environ.get("ML_BASE_URL") or "").strip().rstrip("/")
    if not base:
        return 0.0
    url = f"{base.rstrip('/')}/predict"
    body = json.dumps({"top": top_hex, "bottom": bottom_hex}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(exc.read().decode("utf-8", errors="replace")) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc
    if not payload.get("ok"):
        raise RuntimeError(str(payload.get("error", "ml_error")))
    return float(payload["score"])


def require_login():
    """Redirect to login page if the user is not authenticated."""
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return None


def _outfit_request_fields():
    """Return (top, bottom, photo_b64, timestamp) from JSON body."""
    body = request.get_json(silent=True) or {}
    top = (body.get("top") or "").strip()
    bottom = (body.get("bottom") or "").strip()
    return top, bottom, body.get("photo"), body.get("timestamp")


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
    if session.get("user_id"):
        return redirect(url_for("analyze"))
    return redirect(url_for("login"))


@app.route("/api/outfit", methods=["POST"])
def api_save_outfit():
    """Accept JSON outfit payload and persist it to MongoDB."""
    raw_uid = session.get("user_id")
    if not raw_uid:
        return jsonify({"ok": False, "error": "authentication_required"}), 401
    try:
        user_oid = ObjectId(raw_uid)
    except InvalidId:
        return jsonify({"ok": False, "error": "invalid_session"}), 401

    top, bottom, photo_b64, ts = _outfit_request_fields()

    bad_req = None
    if not top or not bottom or not photo_b64:
        bad_req = "top, bottom, and photo are required"
    elif not top.startswith("#") or not bottom.startswith("#"):
        bad_req = "top and bottom must be #RRGGBB hex"
    if bad_req:
        return jsonify({"error": bad_req}), 400

    try:
        score = fetch_coordination_score(top, bottom)
    except RuntimeError as exc:
        return (
            jsonify({"ok": False, "error": "scoring_failed", "detail": str(exc)}),
            503,
        )

    tier = score_to_tier(score)
    qdoc = get_quote_by_tier(tier)

    if not ts:
        ts = datetime.now(timezone.utc).isoformat()

    doc = {
        "user_id": user_oid,
        "top": top,
        "bottom": bottom,
        "coordination_score": score,
        "tier": tier,
        "quote": qdoc["text"] if qdoc else None,
        "quote_id": str(qdoc["_id"]) if qdoc and qdoc.get("_id") else None,
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
            "user_id": str(user_oid),
            "coordination_score": score,
            "tier": tier,
            "quote": qdoc["text"] if qdoc else None,
            "quote_id": str(qdoc["_id"]) if qdoc and qdoc.get("_id") else None,
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
    auth_redirect = require_login()
    if auth_redirect:
        return auth_redirect

    return render_template("analyze.html")


@app.route("/outfits")
def outfits():
    """Render saved outfits for the logged-in user."""
    auth_redirect = require_login()
    if auth_redirect:
        return auth_redirect

    rows = []
    for outfit in reversed(get_outfits_by_user(session.get("user_id"))):
        row = dict(outfit)
        row["id_str"] = str(outfit.get("_id")) if outfit.get("_id") else ""
        row["display_score"] = round(float(outfit.get("coordination_score", 0)) * 100, 1)
        rows.append(row)

    return render_template("outfits.html", outfits=rows)


@app.route("/outfits/<outfit_id>/delete", methods=["POST"])
def delete_outfit(outfit_id):
    """Delete one saved outfit for the logged-in user."""
    auth_redirect = require_login()
    if auth_redirect:
        return auth_redirect
    if delete_outfit_for_user(session.get("user_id"), outfit_id):
        flash("Outfit deleted.", "success")
    else:
        flash("Outfit not found.", "error")
    return redirect(url_for("outfits"))


@app.route("/stats")
def stats():
    """Render the stats page."""
    auth_redirect = require_login()
    if auth_redirect:
        return auth_redirect

    all_outfits = get_all_outfits()
    user_outfits = get_outfits_by_user(session.get("user_id"))

    total = len(all_outfits)
    avg_score = (
        round(
            sum(float(o.get("coordination_score", 0)) * 100 for o in all_outfits) / total,
            1,
        )
        if total
        else 0
    )

    user_total = len(user_outfits)
    user_avg = (
        round(
            sum(float(o.get("coordination_score", 0)) * 100 for o in user_outfits)
            / user_total,
            1,
        )
        if user_total
        else 0
    )

    return render_template(
        "stats.html",
        avg_score=avg_score,
        user_avg=user_avg,
        total_outfits=total,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "3000")), debug=True)
