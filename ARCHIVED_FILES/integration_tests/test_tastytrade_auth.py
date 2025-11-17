#!/usr/bin/env python3
"""
Quick test to verify Tastytrade authentication
"""
import os
from dotenv import load_dotenv
from termcolor import cprint

load_dotenv()

# Test credentials
oauth_token = os.getenv('TASTYTRADE_OAUTH_TOKEN')
oauth_secret = os.getenv('TASTYTRADE_OAUTH_SECRET') or os.getenv('TASTYTRADE_CLIENT_SECRET')
account_number = os.getenv('TASTYTRADE_ACCOUNT_NUMBER')

username = os.getenv('TASTYTRADE_USERNAME')
password = os.getenv('TASTYTRADE_PASSWORD')

cprint(f"\n🔍 Tastytrade Credentials Check:", "cyan")
cprint(f"   USERNAME: {'✅' if username else '❌'} {username}", "cyan")
cprint(f"   PASSWORD: {'✅' if password else '❌'} {'*' * len(password) if password else 'NOT SET'}", "cyan")
cprint(f"   ACCOUNT_NUMBER: {'✅' if account_number else '❌'} {account_number}", "cyan")

if not all([username, password, account_number]):
    cprint("\n❌ Missing credentials!", "red")
    exit(1)

cprint("\n🔐 Testing Tastytrade Session (v9.10)...", "cyan")
try:
    from tastytrade import Session
    
    session = Session(
        login=username,
        password=password
    )
    cprint(f"✅ Session authenticated successfully!", "green")
    cprint(f"   Session token: {session.session_token[:20]}...", "green")
    
except Exception as e:
    cprint(f"❌ Authentication failed: {e}", "red")
    import traceback
    traceback.print_exc()
    exit(1)

cprint("\n✅ All tests passed!", "green")
