#!/usr/bin/env python3
"""
Test different session token formats
"""

import os
import requests
from dotenv import load_dotenv
from termcolor import cprint

load_dotenv()

username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')

base_url = "https://api.tastytrade.com"

# Get session token
cprint("\n📊 Authenticating...", "cyan")
auth_url = f"{base_url}/sessions"
auth_data = {"login": username, "password": password}
response = requests.post(auth_url, json=auth_data, timeout=10)

if response.status_code != 201:
    cprint(f"❌ Auth failed", "red")
    exit(1)

data = response.json()
session_token = data['data']['session-token']
cprint(f"✅ Session token obtained", "green")
cprint(f"   Full response keys: {list(data['data'].keys())}", "cyan")

# Try to validate the session
cprint("\n📊 Testing session validation...", "cyan")

validate_url = f"{base_url}/sessions/validate"

# Try different formats
formats = [
    ("Bearer header", {"Authorization": f"Bearer {session_token}"}),
    ("Cookie Session", {"Cookie": f"Session={session_token}"}),
    ("Cookie tastyworks", {"Cookie": f"tastyworks={session_token}"}),
    ("X-Session-Token header", {"X-Session-Token": session_token}),
    ("No auth (just validate)", {}),
]

for name, headers in formats:
    try:
        response = requests.post(validate_url, headers=headers, timeout=5)
        cprint(f"\n{name}:", "cyan")
        cprint(f"   Status: {response.status_code}", "cyan")
        if response.status_code in [200, 201]:
            cprint(f"   ✅ SUCCESS!", "green")
            cprint(f"   Response: {response.text[:200]}", "green")
        else:
            cprint(f"   Response: {response.text[:100]}", "yellow")
    except Exception as e:
        cprint(f"\n{name}: Error - {e}", "red")

cprint("\n" + "="*60, "cyan")
