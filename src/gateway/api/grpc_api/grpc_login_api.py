import os
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session, make_response

from shared.logger import get_logger
from clients.grpc.auth_client import AuthGrpcClient

logger = get_logger("grpc_login_api")

grpc_login_api = Blueprint("grpc_login_api", __name__)
grpc_client = AuthGrpcClient()


@grpc_login_api.route("/grpc-login", methods=["GET", "POST"])
def grpc_login():
    logger.info("Received gRPC login request")

    if request.method == "GET":
        return render_template("grpc_login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    try:
        logger.info(f"Calling Auth via gRPC: user={username}")
        response = grpc_client.login(username, password)

        if not response.token:
            flash("Invalid credentials.", "danger")
            return redirect(url_for("grpc_login_api.grpc_login"))

        token = response.token

        session["token"] = token
        resp = make_response(redirect(url_for("upload_api.upload")))
        resp.set_cookie(
            "access_token",
            token,
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=24 * 60 * 60
        )

        logger.info("gRPC login success!")
        flash("gRPC login successful!", "success")
        return resp

    except Exception as e:
        logger.error(f"gRPC login failed: {e}")
        flash("gRPC server error.", "danger")
        return redirect(url_for("grpc_login_api.grpc_login"))
