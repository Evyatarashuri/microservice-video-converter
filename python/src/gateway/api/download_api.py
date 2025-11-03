import os, gridfs, pika, json
from flask import Blueprint, request, send_file, render_template, redirect, url_for, send_file, flash
from flask_pymongo import PyMongo
from auth import validate
from api import login_api, upload_api, register_api
from python.src.gateway.clients.rest import auth_client
from services import util
from bson.objectid import ObjectId
from shared.logger import get_logger
import requests

logger = get_logger("download_api")
download_api = Blueprint("download_api", __name__)

mongo_video = PyMongo(server, uri=os.getenv("MONGO_URI_VIDEO"))
mongo_mp3 = PyMongo(server, uri=os.getenv("MONGO_URI_MP3"))

fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

# ==== download route =====
@download_api.route("/download", methods=["GET"])
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