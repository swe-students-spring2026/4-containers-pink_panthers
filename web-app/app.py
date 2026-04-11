# pylint: disable=missing-module-docstring,missing-function-docstring

import os
from types import SimpleNamespace
from flask import Flask, redirect, render_template, url_for, jsonify
from db import get_latest

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")


@app.context_processor
def _ctx():
    # base.html shows nav when current_user.is_authenticated
    return {"current_user": SimpleNamespace(is_authenticated=True, id="guest")}


@app.route("/")
def index():
    return redirect(url_for("analyze"))


@app.route("/latest")
def latest():
    """Show the latest analysis result."""
    data = get_latest()
    if not data:
        return "No results found"

    data["_id"] = str(data["_id"])
    return str(data)

@app.route("/results")
def results():
    """Return latest analysis result as JSON."""
    data = get_latest()

    if not data:
        return jsonify({"message": "No results found"}), 404

    data["_id"] = str(data["_id"])
    return jsonify(data)


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
