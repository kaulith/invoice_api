import os
from dotenv import load_dotenv

load_dotenv()

# ARN API
ARN_API_KEY = os.getenv("ARN_API_KEY")
ARN_API_URL = os.getenv("ARN_API_URL")

# e-invoice
EINVOICE_API_KEY = os.getenv("EINVOICE_API_KEY")
EINVOICE_API_SECRET = os.getenv("EINVOICE_API_SECRET")
EINVOICE_API_URL = os.getenv("EINVOICE_API_URL")

# Flask / Session Config
SECRET_KEY = os.getenv("SECRET_KEY")
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False") == "True"
SESSION_COOKIE_HTTPONLY = os.getenv("SESSION_COOKIE_HTTPONLY", "True") == "True"
PERMANENT_SESSION_LIFETIME = int(os.getenv("PERMANENT_SESSION_LIFETIME", 604800))  
