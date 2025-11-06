import os, jwt, datetime, bcrypt
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from shared.logger import get_logger
from models import User

logger = get_logger("auth")

# ==============================
# Flask setup
# ==============================
server = Flask(__name__)

# ==============================
# Database configuration
# (values are injected via ConfigMap + Secret)
# ==============================
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PW = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "auth_db")
JWT_SECRET = os.getenv("JWT_SECRET")

server.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PW}@{POSTGRES_HOST}/{POSTGRES_DB}"
)
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(server)


# ==============================
# Helper functions
# ==============================
def create_jwt(username, secret, is_admin):
    payload = {
        "username": username,
        "exp": datetime.datetime.now(tz=datetime.timezone.utc)
        + datetime.timedelta(days=1),
        "iat": datetime.datetime.now(tz=datetime.timezone.utc),
        "admin": is_admin,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


# ==============================
# Routes
# ==============================

@server.route("/register", methods=["POST"])
def register():
    logger.info("Received registration request")

    data = request.get_json()
    email = data.get("username")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 409

    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    new_user = User(email=email, password=hashed_pw)

    db.session.add(new_user)
    db.session.commit()

    logger.info(f"User {email} registered successfully")
    return jsonify({"message": "User registered successfully"}), 201


@server.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    logger.info(f"AUTH HEADER: {auth}")

    if not auth or not auth.username or not auth.password:
        logger.warning("Missing credentials")
        return jsonify({"error": "Missing credentials"}), 401

    user = User.query.filter_by(email=auth.username).first()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if bcrypt.checkpw(auth.password.encode("utf-8"), user.password.encode("utf-8")):
        token = create_jwt(user.email, JWT_SECRET, True)
        logger.info(f"Login successful for user: {user.email}")
        return jsonify({"token": token}), 200
    else:
        logger.warning(f"Invalid credentials for user: {auth.username}")
        return jsonify({"error": "Invalid credentials"}), 401


@server.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers.get("Authorization")

    if not encoded_jwt:
        return jsonify({"error": "Missing credentials"}), 401

    try:
        token = encoded_jwt.split(" ")[1]
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return jsonify(decoded), 200
    except Exception as e:
        logger.error(f"JWT validation failed: {e}")
        return jsonify({"error": "Not authorized"}), 403


# ==============================
# Application entry point
# ==============================
if __name__ == "__main__":
    logger.info("Starting auth service...")
    server.run(host="0.0.0.0", port=5000)
