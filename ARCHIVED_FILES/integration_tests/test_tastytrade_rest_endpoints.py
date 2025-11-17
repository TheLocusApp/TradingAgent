#!/usr/bin/env python3
"""Test different Tastytrade REST endpoints"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')

# Authenticate
print("🔐 Authenticating...")
url = "https://api.tastytrade.com/sessions"
payload = {"login": username, "password": password, "remember-me": True}

response = requests.post(url, json=payload, timeout=10)
data = response.json()
session_token = data['data']['session-token']
print(f"✅ Authenticated")

headers = {"Authorization": f"Bearer {session_token}"}

# Test different endpoints
endpoints = [
    "/market-data/quotes/QQQ",
    "/market-data/quotes/.QQQ251104C621",
    "/instruments/equities/QQQ/options/QQQ%20%20%20251104C00621000",
]

for endpoint in endpoints:
    print(f"\n📍 Testing: {endpoint}")
    try:
        response = requests.get(f"https://api.tastytrade.com{endpoint}", headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Success!")
            print(json.dumps(response.json(), indent=2)[:500])
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
