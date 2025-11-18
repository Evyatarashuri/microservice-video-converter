import gridfs
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, send_file
from bson.objectid import ObjectId
from io import BytesIO
from shared.logger import get_logger

logger = get_logger("download_api")

download_api = Blueprint("download_api", __name__)

download_api.mongo_video = None
download_api.mongo_mp3 = None
download_api.fs_videos = None
download_api.fs_mp3s = None


@download_api.route("/download", methods=["GET"])
def download_page():
    """Render the download page, check if MP3 is ready or still processing."""
    fid_string = request.args.get("fid")

    if not fid_string:
        logger.warning("No fid provided in /download request")
        return render_template("download.html", fid=None, status=None)

    try:
        fs_mp3s = download_api.fs_mp3s
        file = fs_mp3s.find_one({"_id": ObjectId(fid_string)})

        if file:
            logger.info(f"MP3 file found for fid={fid_string}")
            return render_template("download.html", fid=fid_string, status="ready")

        logger.info(f"MP3 not found yet for fid={fid_string}, still processing...")
        flash("Conversion still in progress. Please wait...", "info")
        return render_template("download.html", fid=fid_string, status="processing")

    except Exception as err:
        logger.error(f"Failed to retrieve file from GridFS: {err}")
        flash("Error retrieving file status.", "danger")
        return redirect(url_for("upload_api.upload"))


@download_api.route("/download/<fid>", methods=["GET"])
def download_mp3(fid):
    """Return the actual MP3 file for playback or download."""
    try:
        fs_mp3s = download_api.fs_mp3s
        file = fs_mp3s.get(ObjectId(fid))
        logger.info(f"Streaming MP3 file {fid}")
        return send_file(BytesIO(file.read()), mimetype="audio/mpeg", download_name=f"{fid}.mp3")
    except Exception as e:
        logger.error(f"Error downloading MP3 file {fid}: {e}")
        flash("File not found or not ready yet.", "danger")
        return redirect(url_for("upload_api.upload"))


@download_api.route("/api/status", methods=["GET"])
def check_status():
    """AJAX polling endpoint — checks if MP3 file is available in GridFS."""
    fid_string = request.args.get("fid")
    if not fid_string:
        return jsonify({"ready": False}), 400

    try:
        fs_mp3s = download_api.fs_mp3s
        fs_mp3s.get(ObjectId(fid_string))
        logger.info(f"File {fid_string} is ready for download.")
        return jsonify({"ready": True}), 200
    except Exception:
        return jsonify({"ready": False}), 200
