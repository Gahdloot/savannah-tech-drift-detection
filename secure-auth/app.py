import requests
import json
import datetime
import time
import os
import logging
from functools import wraps
from flask import Flask, request, session, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
from flask_talisman import Talisman
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_principal import Principal, Permission, RoleNeed
from marshmallow import Schema, fields, validate
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

###GLOBAL VARIABLES TO SET###
#resource name from AAD
resourcename = os.getenv("RESOURCE")

#client name from AAD
clientid = os.getenv("CLIENTID")

#token endpoint from AAD
tokenendpoint = os.getenv("TOKEN_ENDPOINT")

#length of time in seconds before token expires to request a refresh
timebeforerefresh = os.getenv("REFRESH_TIME", 600) #default to 10 minutes

# Security configurations
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", 5))
LOGIN_TIMEOUT = int(os.getenv("LOGIN_TIMEOUT", 300))  # 5 minutes
SESSION_LIFETIME = int(os.getenv("SESSION_LIFETIME", 3600))  # 1 hour

##### DO NOT EDIT BELOW THIS LINE #####

# Configure logging
logging.basicConfig(
    filename='auth_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

#port number on which to listen
portnumber = 5000

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", Fernet.generate_key().decode())
app.config['SESSION_TYPE'] = 'redis'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(seconds=SESSION_LIFETIME)

# Initialize security extensions
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
Session(app)
Talisman(app,
    force_https=True,
    strict_transport_security=True,
    session_cookie_secure=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self'",
        'style-src': "'self'"
    }
)
login_manager = LoginManager()
login_manager.init_app(app)
Principal(app)

# Define roles and permissions
admin_role = RoleNeed('admin')
user_role = RoleNeed('user')
admin_permission = Permission(admin_role)
user_permission = Permission(user_role)

# Schema for request validation
class TokenRequestSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3))
    password = fields.Str(required=True, validate=validate.Length(min=8))

# Secure token storage
class SecureTokenStorage:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
    
    def encrypt_token(self, token):
        return self.cipher_suite.encrypt(token.encode())
    
    def decrypt_token(self, encrypted_token):
        return self.cipher_suite.decrypt(encrypted_token).decode()

# User model
class User(UserMixin):
    def __init__(self, username, roles=None):
        self.id = username
        self.roles = roles or ['user']
        self.login_attempts = 0
        self.locked_until = None

# Token class with enhanced security
class Token(object):
    def __init__(self, accesstoken=None, refreshtoken=None, expires_on=None, username=None, password=None):
        self.accesstoken = accesstoken
        self.refreshtoken = refreshtoken
        self.expires_on = expires_on
        self.username = username
        self.password = password
        self.created_at = datetime.datetime.utcnow()
        self.last_used = datetime.datetime.utcnow()

# Create secure token storage instance
token_storage = SecureTokenStorage()

# Create an empty list to hold retrieved tokens
tokens = []

# User loader for Flask-Login
@login_manager.user_loader
def load_user(username):
    # In a real application, this would load from a database
    return User(username)

# Rate limiting decorator
def rate_limit_by_ip():
    return limiter.limit("5 per minute")

# Permission decorator
def require_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not permission.can():
                return jsonify({"error": "Permission denied"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Audit logging decorator
def audit_log(action):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logger.info(f"Action: {action}, User: {request.remote_addr}, Time: {datetime.datetime.utcnow()}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Enhanced token retrieval function
def gettokenfromazure(action, userreq, refreshtoken):
    try:
        tokenpost = {}
        if action == "new":
            tokenpost = {
                'client_id': clientid,
                'resource': resourcename,
                'username': userreq['username'],
                'password': userreq['password'],
                'grant_type': 'password'
            }
        else:
            tokenpost = {
                'client_id': clientid,
                'resource': resourcename,
                'refresh_token': refreshtoken,
                'grant_type': 'refresh_token'
            }

        tokenres = requests.post(tokenendpoint, data=tokenpost)
        tokenres.raise_for_status()

        mytoken = Token()
        mytoken.accesstoken = token_storage.encrypt_token(tokenres.json()['access_token'])
        mytoken.refreshtoken = token_storage.encrypt_token(tokenres.json()['refresh_token'])
        mytoken.username = userreq['username']
        mytoken.password = userreq['password']
        mytoken.expires_on = tokenres.json()['expires_on']
        
        logger.info(f"Token retrieved successfully for user: {userreq['username']}")
        return mytoken
    except requests.exceptions.RequestException as e:
        logger.error(f"Token retrieval failed: {str(e)}")
        errorobj = Expando()
        errorobj.error = "error"
        errorobj.description = str(e)
        return errorobj

# Enhanced token response generation
def generatetokenresponse(token, action):
    tokenobj = Expando()
    tokenobj.accesstoken = token_storage.decrypt_token(token.accesstoken)
    tokenobj.expires_on = token.expires_on
    tokenobj.action = {
        "refresh": "refreshed existing token",
        "existing": "returned existing token",
        "new": "retrieved new token",
        "expired": "retrieved new token to replace expired token"
    }.get(action, "unknown action")

    return json.dumps(tokenobj.__dict__)

# Enhanced token request endpoint
@app.route('/requesttoken', methods=['GET', 'POST'])
@rate_limit_by_ip()
@audit_log("token_request")
def requesttoken():
    try:
        # Validate request data
        schema = TokenRequestSchema()
        userreq = schema.load(request.get_json(silent=True))
        
        # Check for existing token
        existingtokens = list(filter(lambda x: x.username == userreq['username'], tokens))
        
        if len(existingtokens) > 0:
            existingtoken = existingtokens[0]
            
            if float(existingtoken.expires_on) < time.time():
                tokens.remove(existingtoken)
                newtoken = gettokenfromazure("new", userreq, None)
                response = generatetokenresponse(newtoken, "expired")
                tokens.append(newtoken)
                return response
            
            if (float(existingtoken.expires_on) - time.time()) < float(timebeforerefresh):
                refreshedtoken = gettokenfromazure("refresh", userreq, existingtoken.refreshtoken)
                response = generatetokenresponse(refreshedtoken, "refresh")
                tokens.remove(existingtoken)
                tokens.append(refreshedtoken)
                return response
            else:
                response = generatetokenresponse(existingtoken, "existing")
                return response
        else:
            newtoken = gettokenfromazure("new", userreq, None)
            response = generatetokenresponse(newtoken, "new")
            tokens.append(newtoken)
            return response
            
    except Exception as e:
        logger.error(f"Error in requesttoken: {str(e)}")
        return jsonify({"error": str(e)}), 400

# Logout endpoint
@app.route('/logout', methods=['POST'])
@login_required
@audit_log("logout")
def logout():
    logout_user()
    session.clear()
    return jsonify({"message": "Successfully logged out"}), 200

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=portnumber)