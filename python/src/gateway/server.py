import os, gridfs, pika, json
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util
from bson.objectid import ObjectId
from monitoring.logger import get_logger

logger = get_logger("gateway")

server = Flask(__name__)

mongo_video = PyMongo(server, uri="mongodb://mongodb:27017/videos")
mongo_mp3 = PyMongo(server, uri="mongodb://mongodb:27017/mp3s")

fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()

# login route
@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)

    if not err:
        return token
    else:
        return err

# upload route
@server.route("/upload", methods=["POST"])
def upload():

    logger.info("Received upload request")

    access, err = validate.token(request)

    if err:
        logger.error(f"Token validation failed: {err}")
        return err

    access = json.loads(access)

    if access["admin"]:
        if len(request.files) > 1 or len(request.files) < 1:
            logger.error("Invalid number of files uploaded.")
            return "exactly 1 file required", 400

        for _, f in request.files.items():
            err = util.upload(f, fs_videos, channel, access)

            if err:
                logger.error(f"File upload failed: {err}")
                return err

        logger.info("File upload successful.")
        return "success!", 200
    else:
        return "not authorized", 401

# download route
@server.route("/download", methods=["GET"])
def download():

    logger.info("Received download request")

    access, err = validate.token(request)

    if err:
        logger.error(f"Token validation failed: {err}")
        return err

    access = json.loads(access)

    if access["admin"]:
        fid_string = request.args.get("fid")

        if not fid_string:
            logger.error("fid is required")
            return "fid is required", 400

        try:
            out = fs_mp3s.get(ObjectId(fid_string))
            return send_file(out, download_name=f"{fid_string}.mp3")
        except Exception as err:
            logger.error(f"Failed to retrieve file from GridFS: {err}")
            return "internal server error", 500

    return "not authorized", 401


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)