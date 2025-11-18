import os
import json
import gridfs
from flask import Flask, render_template
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

# ====== Internal Imports ======
from shared.rabbit import RabbitMQConnection
from api import login_api, register_api, download_api
from api.upload_api import create_upload_blueprint


# =========================================
# Flask Application Setup
# =========================================
server = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

# Secret key for session management
server.secret_key = os.getenv("SECRET_KEY")


# =========================================
# MongoDB Configuration
# =========================================
server.config["MONGO_URI_VIDEO"] = os.getenv("MONGO_URI_VIDEO")
server.config["MONGO_URI_MP3"] = os.getenv("MONGO_URI_MP3")

# Database names for GridFS (used internally)
server.config["MONGO_VIDEO_DB"] = "videos"
server.config["MONGO_MP3_DB"] = "mp3s"

# Initialize Mongo clients
mongo_video = PyMongo(server, uri=server.config["MONGO_URI_VIDEO"])
mongo_mp3 = PyMongo(server, uri=server.config["MONGO_URI_MP3"])

# Initialize GridFS instances
fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

# Attach Mongo clients to download_api blueprint (for file access)
download_api.mongo_video = mongo_video
download_api.mongo_mp3 = mongo_mp3
download_api.fs_videos = gridfs.GridFS(mongo_video.db)
download_api.fs_mp3s = gridfs.GridFS(mongo_mp3.db)

# =========================================
# RabbitMQ Connection (Shared Channel)
# ==========================================
rabbit_connection = RabbitMQConnection()
rabbit_connection.connect()


# =========================================
# Blueprint Registration (Dependency Injection)
# =========================================
upload_blueprint = create_upload_blueprint(rabbit_connection)

server.register_blueprint(login_api)
server.register_blueprint(register_api)
server.register_blueprint(upload_blueprint)
server.register_blueprint(download_api)

@server.route("/")
def home():
    return render_template("home.html")

# =========================================
# Application Entry Point
# =========================================
if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
