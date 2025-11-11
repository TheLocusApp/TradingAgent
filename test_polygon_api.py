#!/usr/bin/env python3
"""Test Polygon API for options data"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('POLYGON_API_KEY')

if not API_KEY:
    print("❌ POLYGON_API_KEY not found in .env")
    exit(1)

print(f"🔑 API Key: {API_KEY[:10]}...")

# Test 1: Get QQQ price
print("\n📊 Test 1: Get QQQ underlying price")
url = "https://api.polygon.io/v2/aggs/ticker/QQQ/prev"
params = {'apiKey': API_KEY}
try:
    response = requests.get(url, params=params, timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data.get('results'):
            price = data['results'][0].get('c')
            print(f"   ✅ QQQ Price: ${price}")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

# Test 2: Get option quote (CALL)
print("\n📊 Test 2: Get QQQ CALL option quote")
option_ticker = "O:QQQ251104C00630000"
url = f"https://api.polygon.io/v3/quotes/{option_ticker}"
params = {'apiKey': API_KEY}
try:
    response = requests.get(url, params=params, timeout=10)
    print(f"   URL: {url}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data.get('results'):
            result = data['results'][0]
            bid = result.get('bid_price', 0)
            ask = result.get('ask_price', 0)
            mid = (bid + ask) / 2 if bid and ask else 0
            print(f"   ✅ CALL Quote: Bid=${bid}, Ask=${ask}, Mid=${mid:.2f}")
        else:
            print(f"   ⚠️ No results in response")
    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

# Test 3: Get option quote (PUT)
print("\n📊 Test 3: Get QQQ PUT option quote")
option_ticker = "O:QQQ251104P00630000"
url = f"https://api.polygon.io/v3/quotes/{option_ticker}"
params = {'apiKey': API_KEY}
try:
    response = requests.get(url, params=params, timeout=10)
    print(f"   URL: {url}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data.get('results'):
            result = data['results'][0]
            bid = result.get('bid_price', 0)
            ask = result.get('ask_price', 0)
            mid = (bid + ask) / 2 if bid and ask else 0
            print(f"   ✅ PUT Quote: Bid=${bid}, Ask=${ask}, Mid=${mid:.2f}")
        else:
            print(f"   ⚠️ No results in response")
    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

print("\n✅ API Test Complete")
