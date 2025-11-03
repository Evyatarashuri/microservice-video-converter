import os, gridfs, pika, json
from flask import Blueprint, request, send_file, render_template, redirect, url_for, send_file, flash
from flask_pymongo import PyMongo
from auth import validate
from api import login_api, upload_api
from python.src.gateway.clients.rest import auth_client
from services import util
from bson.objectid import ObjectId
from shared.logger import get_logger
import requests

logger = get_logger("register_api")

register_api = Blueprint("register_api", __name__)


# ==== register route =====
@register_api.route("/register", methods=["GET", "POST"])
def register():
    logger.info("Received registration request")

    if request.method == "GET":
        return render_template("register.html")

    # Get form data
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        logger.warning("Registration failed: Missing username or password")
        flash("Missing username or password", "danger")
        return redirect(url_for("register")), 400
    
    try:
        # Call the auth service microservice

        auth_url = os.getenv("AUTH_SERVICE_URL", "http://auth:5000/register")
        response = requests.post(auth_url, json={"username": username, "password": password})

        # Check response from auth service
        if response.status_code == 201:
            flash("Registration successful!", "success")
            logger.info(f"User registered successfully: {username}")
            return redirect(url_for("login"))
        else:
            msg = response.json().get("message", "Registration failed")
            flash(msg, "danger")
            logger.error(f"User registration failed: {username}: {msg}")
            return redirect(url_for("register")), 400

    except Exception as e:
        logger.error(f"Error occurred during registration: {e}")
        flash("An error occurred", "danger")
        return redirect(url_for("register")), 500