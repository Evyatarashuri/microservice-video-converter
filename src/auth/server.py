import jwt, datetime, os
from flask import Flask, request
from flask_mysqldb import MySQL
import bcrypt, jsonify
from shared.logger import get_logger

logger = get_logger("auth")

server = Flask(__name__)
mysql = MySQL(server)

# config
server.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
server.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
server.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
server.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'auth_db')
server.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))

# login function route
@server.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    logger.info(f"AUTH HEADER: {auth}")

    if not auth or not auth.username or not auth.password:
        logger.warning("Missing credentials")
        return "Missing credentials", 401

    username = auth.username
    password = auth.password

    logger.info("Login attempt for user: %s", username)

    cur = mysql.connection.cursor()
    res = cur.execute(
        "SELECT email, password FROM users WHERE email=%s", (username,)
    )

    if res > 0:
        user_row = cur.fetchone()
        email = user_row[0]
        db_password = user_row[1]

        if password == db_password:
            token = createJWT(username, os.environ.get('JWT_SECRET'), True)
            return token
        else:
            return "Invalid credentials", 401
    else:
        return "Invalid credentials", 401

    

# ==== register route ====
@server.route("/register", methods=["POST"])
def register():

    logger.info("Received registration request")

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    cur = mysql.connection.cursor()

    res = cur.execute(
        "SELECT email FROM users WHERE email=%s", (username,)
    )
    if res:
        return "User already exists", 409
    
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    cur.execute(
        "INSERT INTO users (email, password) VALUES (%s, %s)",
        (username, hashed_pw)
    )
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "User registered successfully"}), 201



# validate jwt function route
@server.route('/validate', methods=['POST'])
def validate():
    encoded_jwt = request.headers["Authorization"]

    if not encoded_jwt:
        return "Missing credentials", 401
    
    encoded_jwt = encoded_jwt.split(" ")[1]

    try:
        decoded = jwt.decode(
            encoded_jwt,
            os.environ.get('JWT_SECRET'),
            algorithms=['HS256']
        )
    except:
        return "Not authorized", 403
    
    return decoded, 200


# create jwt function
def createJWT(username, secret, authz):
    return jwt.encode(
        {
            'username': username,
            'exp': datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
            'iat': datetime.datetime.now(tz=datetime.timezone.utc),
            'admin': authz
        },
        secret,
        algorithm='HS256'
    )


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5000)