#!/usr/bin/env python3
"""Debug Tastytrade authentication response"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')

if not username or not password:
    print("❌ Missing credentials")
    exit(1)

print(f"🔐 Authenticating as {username}...")

url = "https://api.tastytrade.com/sessions"
payload = {
    "login": username,
    "password": password,
    "remember-me": True
}

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"\nStatus: {response.status_code}")
    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"❌ Error: {e}")
