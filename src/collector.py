import requests
import json
import os
from datetime import datetime
from config import settings
from src.auth import get_headers

def get_users():
    url = f"{settings.API_BASE_URL}users"
    response = requests.get(url, headers=get_headers())
    return response.json()

def save_snapshot(data, label):
    os.makedirs(settings.SNAPSHOT_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S')
    file_path = f"{settings.SNAPSHOT_DIR}{label}_{timestamp}.json"
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    return file_path