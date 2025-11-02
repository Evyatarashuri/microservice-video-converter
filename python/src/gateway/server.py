import os, gridfs, pika, json
from flask import Flask, request, send_file, render_template, redirect, url_for, session, send_file, flash
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util
from bson.objectid import ObjectId
from shared.logger import get_logger
import requests

logger = get_logger("gateway")

server = Flask(__name__,
               template_folder="templates",
               static_folder="static"
            )

server.secret_key = os.getenv("SECRET_KEY", "mysecret")

mongo_video = PyMongo(server, uri="mongodb://mongodb:27017/videos")
mongo_mp3 = PyMongo(server, uri="mongodb://mongodb:27017/mp3s")

fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()

# ====== routes ===========================


# ===== login route ======
@server.route("/login", methods=["GET", "POST"])
def login():

    logger.info("Received login request")

    if request.method == "GET":
        return render_template("login.html")
    
    username = request.form.get("username")
    password = request.form.get("password")

    logger.info(f"Attempting login for user: {username}")

    token, err = access.login(request)

    if not err:
        session["token"] = token
        flash("Login successful!", "success")
        logger.info(f"Login successful for user: {username}")
        return redirect(url_for("upload_page"))
    else:
        flash("Invalid credentials", "danger")
        logger.warning(f"Login failed for user: {username}")
        return redirect(url_for("login"))


# ===== upload page route =====
@server.route("/upload", methods=["GET", "POST"])
def upload():

    logger.info("Received upload page request")

    if request.method == "GET":
        return render_template("upload.html")

    logger.info("Received upload request")

    access, err = validate.token(request)

    if err:
        flash("Authorization failed", "danger")
        logger.error(f"Token validation failed: {err}")
        return redirect(url_for("login"))

    access = json.loads(access)

    if access["admin"]:
        file = request.files.get("file")
        if not file:
            flash("No file uploaded.", "danger")
            logger.error("No file uploaded.")
            return redirect(url_for("upload_page"))

        err = util.upload(file, fs_videos, channel, access)

        if err:
            logger.error(f"File upload failed: {err}")
            flash(f"File upload failed: {err}", "danger")
            return redirect(url_for("upload_page"))
        
        flash("File uploaded successfully!", "success")
        logger.info("File uploaded successfully")

        return redirect(url_for("download_page"))
    else:
        flash("Not authorized", "danger")
        logger.warning("Unauthorized upload attempt")
        return redirect(url_for("login"))
    

# ==== register route =====
@server.route("/register", methods=["GET", "POST"])
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


# ==== download route =====
@server.route("/download", methods=["GET"])
def download_page():
    fid_string = request.args.get("fid")

    if not fid_string:
        return render_template("download.html", fid=None)

    try:
        out = fs_mp3s.get(ObjectId(fid_string))
        return send_file(out, download_name=f"{fid_string}.mp3")
    
    except Exception as err:
        logger.error(f"Failed to retrieve file from GridFS: {err}")
        flash("File not found", "danger")
        return redirect(url_for("upload_page"))



if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)