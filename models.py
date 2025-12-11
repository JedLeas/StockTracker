import os
import json
import re
from config import DATA_DIR, USERS_FILE

def get_safe_filename(username, file_type):
    if not username: return None
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', username)
    return os.path.join(DATA_DIR, f"{file_type}_{clean_name}.json")

def load_json(filepath):
    if not filepath or not os.path.exists(filepath): return []
    try:
        with open(filepath, 'r') as f: return json.load(f)
    except: return []

def save_json(filepath, data):
    try:
        with open(filepath, 'w') as f: json.dump(data, f, indent=4)
    except: pass

def load_users():
    if not os.path.exists(USERS_FILE): return {}
    try:
        with open(USERS_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f: json.dump(users, f, indent=4)