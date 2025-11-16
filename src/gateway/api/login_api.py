import os
import requests
from flask import Blueprint, request, render_template, redirect, url_for, flash, make_response, session
from shared.logger import get_logger

logger = get_logger("login_api")

login_api = Blueprint("login_api", __name__)

# ===== LOGIN ROUTE =====
@login_api.route("/login", methods=["GET", "POST"])
def login():
    logger.info("Received login request")

    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    logger.info(f"Received credentials: username={username}, password={'***' if password else None}")
    logger.info(f"Attempting login for user: {username}")

    try:
        response = requests.post(
            f"http://{os.getenv('AUTH_SVC_ADDRESS', 'auth:5000')}/login",
            auth=(username, password)
        )

        if response.status_code == 200:
            token = response.text
            logger.info(f"Login successful for user: {username}")

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

            flash("Login successful!", "success")
            return resp

        elif response.status_code == 401:
            flash("Invalid credentials, please try again.", "danger")
            logger.warning(f"Login failed for user: {username}, status 401")
            return redirect(url_for("login_api.login"))

        else:
            flash("Authentication service error.", "warning")
            logger.error(f"Unexpected status {response.status_code} from auth service.")
            return redirect(url_for("login_api.login"))

    except Exception as e:
        logger.error(f"Login error: {e}")
        flash("Server error, please try again later.", "danger")
        return redirect(url_for("login_api.login"))


# ===== LOGOUT ROUTE =====
@login_api.route("/logout")
def logout():
    """Logout route that clears the session and cookies"""
    logger.info("User logged out")

    resp = make_response(redirect(url_for("login_api.login")))
    resp.delete_cookie("access_token")
    session.pop("token", None)
    flash("Logged out successfully!", "info")

    return resp
