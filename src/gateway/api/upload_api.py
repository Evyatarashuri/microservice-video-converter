import os
import json
import time
import gridfs
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_pymongo import PyMongo
from services import util
from shared.logger import get_logger
from clients.rest import auth_client

logger = get_logger("upload_api")


def create_upload_blueprint(rabbit_connection):
    """
    Creates the upload blueprint with RabbitMQ dependency injection.
    Mongo and GridFS are initialized later once the blueprint is registered to the Flask app.
    """
    upload_api = Blueprint("upload_api", __name__)

    mongo_video = PyMongo()
    fs_videos = None

    @upload_api.record_once
    def on_load(state):
        nonlocal fs_videos
        app = state.app
        mongo_video.init_app(app, uri=os.getenv("MONGO_URI_VIDEO"))
        fs_videos = gridfs.GridFS(mongo_video.db)

    # ======== Routes ========
    @upload_api.route("/upload", methods=["GET", "POST"])
    def upload():
        logger.info("Received upload request")

        if request.method == "GET":
            return render_template("upload.html")

        # ======== Token Validation ========
        access, err = auth_client.validate_token(request)
        if err:
            flash("Authorization failed", "danger")
            logger.error(f"Token validation failed: {err}")
            return redirect(url_for("login_api.login"))

        access = json.loads(access)
        if not access.get("admin"):
            flash("Not authorized", "danger")
            logger.warning("Unauthorized upload attempt")
            return redirect(url_for("login_api.login"))

        # ======== File Handling ========
        file = request.files.get("file")
        if not file:
            flash("No file uploaded.", "danger")
            logger.error("No file uploaded.")
            return redirect(url_for("upload_api.upload"))

        try:
            channel = rabbit_connection.get_channel()
            file_id = util.upload(file, fs_videos, channel, access)
            if not file_id:
                raise Exception("Upload failed (no file_id returned)")

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            flash("File upload failed", "danger")
            return redirect(url_for("upload_api.upload"))

        # ======== Success ========
        flash("File uploaded successfully!", "success")
        logger.info(f"File uploaded successfully with ID: {file_id}")

        # Redirect to download page with fid param
        time.sleep(1.5)
        return redirect(url_for("download_api.download_page", fid=file_id))

    return upload_api
