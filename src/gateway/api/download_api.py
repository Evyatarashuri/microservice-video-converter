import gridfs
import time
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, send_file
from bson.objectid import ObjectId
from io import BytesIO
from shared.logger import get_logger

logger = get_logger("download_api")

download_api = Blueprint("download_api", __name__, url_prefix="/download")

download_api.mongo_video = None
download_api.mongo_mp3 = None
download_api.fs_videos = None
download_api.fs_mp3s = None


@download_api.route("/", methods=["GET"])
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


@download_api.route("/mp3/<mp3_fid>", methods=["GET"])
def stream_mp3(mp3_fid):
    """Streams the MP3 file for playback or download."""
    try:
        fs_mp3s = download_api.fs_mp3s
        if fs_mp3s is None:
            logger.error("GridFS not initialized for MP3s.")
            return "Internal Server Error", 500

        logger.info(f"Streaming MP3 file: {mp3_fid}")
        grid_out = fs_mp3s.get(ObjectId(mp3_fid))

        return send_file(
            BytesIO(grid_out.read()),
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name=f"{mp3_fid}.mp3"
        )

    except gridfs.errors.NoFile:
        logger.warning(f"MP3 file not found in GridFS: {mp3_fid}")
        return "File not found", 404

    except Exception as e:
        logger.error(f"Error while streaming MP3 file: {e}")
        return "Error while retrieving MP3 file", 500


@download_api.route("/api/status", methods=["GET"])
def check_status():
    """Improved status check with stabilization delay"""
    fid_string = request.args.get("fid")
    if not fid_string:
        return jsonify({"ready": False}), 400

    try:
        fs_mp3s = download_api.fs_mp3s
        db = download_api.mongo_video.db

        record = db.conversions.find_one({"video_fid": fid_string})
        if record and "mp3_fid" in record:
            mp3_fid = record["mp3_fid"]

            for attempt in range(3):
                try:
                    fs_mp3s.get(ObjectId(mp3_fid))
                    logger.info(f"MP3 file ready in GridFS for fid={mp3_fid}")
                    return jsonify({"ready": True, "mp3_fid": mp3_fid}), 200
                except Exception:
                    logger.warning(f"GridFS not ready yet (attempt {attempt+1})")
                    time.sleep(2)

            logger.info(f"Mapping found but file not yet ready in GridFS for fid={fid_string}")
            return jsonify({"ready": False}), 200

        try:
            fs_mp3s.get(ObjectId(fid_string))
            logger.info(f"MP3 found directly in GridFS for fid={fid_string}")
            return jsonify({"ready": True, "mp3_fid": fid_string}), 200
        except Exception:
            pass

        return jsonify({"ready": False}), 200

    except Exception as e:
        logger.error(f"Error in /api/status: {e}")
        return jsonify({"ready": False}), 500

