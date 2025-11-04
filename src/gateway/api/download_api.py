import gridfs
from flask import Blueprint, request, render_template, redirect, url_for, flash
from bson.objectid import ObjectId
from shared.logger import get_logger

logger = get_logger("download_api")

download_api = Blueprint("download_api", __name__)

mongo_video = None
mongo_mp3 = None
fs_videos = None
fs_mp3s = None


@download_api.route("/download", methods=["GET"])
def download_page():
    fid_string = request.args.get("fid")

    if not fid_string:
        return render_template("download.html", fid=None)

    try:
        out = fs_mp3s.get(ObjectId(fid_string))
        return redirect(url_for("download_api.download_file", fid=fid_string))
    except Exception as err:
        logger.error(f"Failed to retrieve file from GridFS: {err}")
        flash("File not found", "danger")
        return redirect(url_for("upload_api.upload"))


@download_api.route("/download/<fid>", methods=["GET"])
def download_file(fid):
    """Actual route that streams the file from GridFS"""
    try:
        out = fs_mp3s.get(ObjectId(fid))
        return out.read()
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return "File not found", 404
