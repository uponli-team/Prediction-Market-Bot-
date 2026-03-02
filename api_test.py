import requests
import json
print("Testing Gamma API...")
r = requests.get("https://gamma-api.polymarket.com/markets", params={"active": "true", "limit": 5})
print("Gamma Status:", r.status_code)
if r.status_code == 200:
    for m in r.json()[:2]:
        mid = m["id"]
        print("Market:", m.get("question", "N/A"), mid)
        try:
            p = requests.get(f"https://clob.polymarket.com/prices?market={mid}")
            print("CLOB:", p.status_code, p.text[:100])
        except Exception as e:
            print("CLOB error:", e)
