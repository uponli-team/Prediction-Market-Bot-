import requests
import json
try:
    markets = requests.get('https://gamma-api.polymarket.com/markets', params={'active':'true','limit':1}).json()
    with open('market_dump.json', 'w') as f:
        json.dump(markets, f, indent=2)
except Exception as e:
    with open('market_dump.json', 'w') as f:
        f.write(str(e))
