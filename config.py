import os
import pytz
from datetime import time as dtime

SECRET_KEY = os.environ.get("SECRET_KEY")
PUSHOVER_APP_TOKEN = os.environ.get("PUSHOVER_APP_TOKEN")
CRON_SECRET = os.environ.get("CRON_SECRET")

if os.environ.get("FLASK_DEBUG") != '1':
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application")
    if not CRON_SECRET:
        raise ValueError("No CRON_SECRET set for cron endpoint")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

MARKET_OPEN = dtime(9, 30)
MARKET_CLOSE = dtime(16, 0)
US_EASTERN = pytz.timezone('US/Eastern')