import os, requests, json

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
    token = request.headers.get("Authorization")

    if not token:
        cookie_token = request.cookies.get("access_token")
        if not cookie_token:
            return None, ("Missing authorization (no header or cookie)", 401)
        
        try:
            data = json.loads(cookie_token)
            token = data.get("token")
        except json.JSONDecodeError:
            token = cookie_token

        token = f"Bearer {token}"

    response = requests.post(
        f"http://{os.getenv('AUTH_SVC_ADDRESS', 'auth:5000')}/validate",
        headers={"Authorization": token}
    )

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)
