# pylint: disable=missing-module-docstring,missing-function-docstring

import os
from types import SimpleNamespace
from db import get_latest

from flask import Flask, redirect, render_template, url_for

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
    return str(data)


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
