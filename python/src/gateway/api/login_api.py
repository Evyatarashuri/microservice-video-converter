from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from auth import validate
from services import util
from flask_pymongo import PyMongo
from shared.logger import get_logger
from clients.rest import auth_client
import json, gridfs

logger = get_logger("login_api")

login_api = Blueprint("login_api", __name__)

# ===== login route ======
@login_api.route("/login", methods=["GET", "POST"])
def login():

    logger.info("Received login request")

    if request.method == "GET":
        return render_template("login.html")
    
    username = request.form.get("username")
    password = request.form.get("password")

    logger.info(f"Attempting login for user: {username}")

    token, err = auth_client.login(request)

    if not err:
        session["token"] = token
        flash("Login successful!", "success")
        logger.info(f"Login successful for user: {username}")
        return redirect(url_for("upload_page"))
    else:
        flash("Invalid credentials", "danger")
        logger.warning(f"Login failed for user: {username}")
        return redirect(url_for("login"))