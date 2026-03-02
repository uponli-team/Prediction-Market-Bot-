import requests
import json
markets = requests.get('https://gamma-api.polymarket.com/markets', params={'active':'true','closed':'false','limit':10}).json()
for m in markets:
    print(f"Market: {m.get('question', 'N/A')[:50]}")
    print(f"Category: {m.get('category')}")
    print(f"Tags: {m.get('tags', [])}")
    print(f"Outcomes: {m.get('outcomes')}")
    print("---")
