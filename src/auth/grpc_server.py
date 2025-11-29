import os
import grpc
import jwt
import bcrypt
from concurrent import futures

from flask import Flask

import auth_pb2
import auth_pb2_grpc

from models import User
from auth.db import db
from shared.logger import get_logger

logger = get_logger("auth-grpc")

# ===========================================
# Flask app for DB session + SQLAlchemy
# ===========================================
app = Flask(__name__)

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PW = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "auth_db")
JWT_SECRET = os.getenv("JWT_SECRET")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PW}@{POSTGRES_HOST}/{POSTGRES_DB}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# ===========================================
# gRPC Auth Service Implementation
# ===========================================
class AuthService(auth_pb2_grpc.AuthServiceServicer):

    def Login(self, request, context):
        logger.info(f"gRPC Login request for user: {request.username}")

        email = request.username
        password = request.password

        with app.app_context():
            user = User.query.filter_by(email=email).first()

            if not user:
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                context.set_details("Invalid credentials")
                return auth_pb2.LoginResponse()

            if not bcrypt.checkpw(password.encode(), user.password.encode()):
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                context.set_details("Invalid credentials")
                return auth_pb2.LoginResponse()

            token = jwt.encode(
                {"username": email},
                JWT_SECRET,
                algorithm="HS256"
            )

            return auth_pb2.LoginResponse(token=token)

    def ValidateToken(self, request, context):
        try:
            decoded = jwt.decode(
                request.token,
                JWT_SECRET,
                algorithms=["HS256"]
            )
            return auth_pb2.ValidateResponse(
                valid=True,
                user_id=decoded.get("username")
            )
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return auth_pb2.ValidateResponse(valid=False)


# ===========================================
# gRPC Server Runner
# ===========================================
def start_grpc_server():
    logger.info("Starting Auth gRPC service...")

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )

    auth_pb2_grpc.add_AuthServiceServicer_to_server(
        AuthService(), server
    )

    server.add_insecure_port("[::]:50051")
    server.start()

    logger.info("Auth gRPC server listening on port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    with app.app_context():
        start_grpc_server()
