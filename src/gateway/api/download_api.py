import gridfs
from flask import Blueprint, request, render_template, redirect, url_for, flash, send_file
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
    fid_string = request.args.get("fid")

    if not fid_string:
        return render_template("download.html", fid=None, status=None)

    try:
        mongo = download_api.mongo_video
        record = mongo.db.conversions.find_one({"video_fid": fid_string})

        if not record or "mp3_fid" not in record:
            logger.info(f"Video {fid_string} still processing or no record found.")
            flash("Conversion still in progress, please try again later.", "warning")
            return render_template("download.html", fid=fid_string, status="processing")

        mp3_fid = record["mp3_fid"]
        logger.info(f"Serving MP3 file for video {fid_string} → mp3_fid={mp3_fid}")

        return render_template("download.html", fid=fid_string, mp3_fid=mp3_fid, status="ready")

    except Exception as err:
        logger.error(f"Failed to retrieve conversion record: {err}")
        flash("File not found", "danger")
        return redirect(url_for("upload_api.upload"))


@download_api.route("/download/mp3/<mp3_fid>", methods=["GET"])
def download_mp3(mp3_fid):
    """Returns the actual MP3 file for download"""
    try:
        fs_mp3s = download_api.fs_mp3s
        file = fs_mp3s.get(ObjectId(mp3_fid))
        logger.info(f"Streaming MP3 file: {mp3_fid}")
        return send_file(BytesIO(file.read()), mimetype="audio/mpeg", download_name=f"{mp3_fid}.mp3")
    except Exception as e:
        logger.error(f"Error downloading MP3 file: {e}")
        flash("File not found or not ready yet", "danger")
        return redirect(url_for("upload_api.upload"))
