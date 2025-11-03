from flask import Blueprint, request, render_template, redirect, url_for, flash
from auth import validate
from services import util
from shared.logger import get_logger
from flask_pymongo import PyMongo
import gridfs, json, os

logger = get_logger("upload_api")

def create_upload_blueprint(rabbit_connection):
    upload_api = Blueprint("upload_api", __name__)

    mongo_video = PyMongo(upload_api, uri=os.getenv("MONGO_URI_VIDEO"))

    fs_videos = gridfs.GridFS(mongo_video.db)

    @upload_api.route("/upload", methods=["GET", "POST"])
    def upload():
        logger.info("Received upload request")

        if request.method == "GET":
            return render_template("upload.html")

        access, err = validate.token(request)
        if err:
            flash("Authorization failed", "danger")
            logger.error(f"Token validation failed: {err}")
            return redirect(url_for("login"))

        access = json.loads(access)

        if not access.get("admin"):
            flash("Not authorized", "danger")
            logger.warning("Unauthorized upload attempt")
            return redirect(url_for("login"))

        file = request.files.get("file")
        if not file:
            flash("No file uploaded.", "danger")
            logger.error("No file uploaded.")
            return redirect(url_for("upload"))

        try:
            channel = rabbit_connection.get_channel()
            err = util.upload(file, fs_videos, channel, access)
            if err:
                raise Exception(err)
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            flash("File upload failed", "danger")
            return redirect(url_for("upload"))

        flash("File uploaded successfully!", "success")
        logger.info("File uploaded successfully")
        return redirect(url_for("download_page"))

    return upload_api

# Note: The function create_upload_blueprint is used for dependency injection of the RabbitMQ connection.