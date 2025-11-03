import os, requests

# === LOGIN ===
def login(request):
    auth = request.authorization
    if not auth:
        return None, ("Missing authorization", 401)

    basicAuth = (auth.username, auth.password)
    response = requests.post(
        f"http://{os.getenv('AUTH_SVC_ADDRESS')}/login",
        auth=basicAuth
    )

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)


# === VALIDATE TOKEN ===
def validate_token(request):
    if "Authorization" not in request.headers:
        return None, ("Missing authorization header", 401)
    
    token = request.headers["Authorization"]
    if not token:
        return None, ("Empty token", 401)
    
    response = requests.post(
        f"http://{os.getenv('AUTH_SVC_ADDRESS')}/validate",
        headers={"Authorization": token}
    )

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)
