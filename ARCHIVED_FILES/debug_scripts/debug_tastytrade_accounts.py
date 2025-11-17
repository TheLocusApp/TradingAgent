#!/usr/bin/env python3
"""Debug Tastytrade accounts endpoint"""

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

# Authenticate
print(f"🔐 Authenticating...")
url = "https://api.tastytrade.com/sessions"
payload = {"login": username, "password": password, "remember-me": True}

response = requests.post(url, json=payload, timeout=10)
data = response.json()
session_token = data['data']['session-token']
print(f"✅ Authenticated")
print(f"   Session token: {session_token[:20]}...")
print(f"   Response keys: {data['data'].keys()}")

# Try different account endpoints with different auth methods
endpoints = [
    "/accounts",
    "/customers/me/accounts",
    "/customers/me",
]

auth_methods = [
    ("Bearer", {"Authorization": f"Bearer {session_token}"}),
    ("Cookie", {"Cookie": f"session-token={session_token}"}),
    ("X-Auth", {"X-Auth-Token": session_token}),
]

for auth_name, headers in auth_methods:
    print(f"\n🔐 Auth method: {auth_name}")
    for endpoint in endpoints:
        print(f"   📍 {endpoint}")
        try:
            response = requests.get(f"https://api.tastytrade.com{endpoint}", headers=headers, timeout=10)
            print(f"      Status: {response.status_code}")
            if response.status_code == 200:
                print(f"      ✅ Success!")
                data = response.json()
                print(json.dumps(data, indent=2)[:300])
        except Exception as e:
            print(f"      ❌ Error: {e}")
