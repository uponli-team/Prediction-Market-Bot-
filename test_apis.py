
import requests
import json
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GAMMA_API = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
COINGECKO_API = "https://api.coingecko.com/api/v3"

def test_gamma_api():
    print("\n--- Testing Gamma API (Active Markets) ---")
    try:
        url = f"{GAMMA_API}/markets?active=true&closed=false&limit=10&order=volumeNum&ascending=false"
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Items returned: {len(data)}")
            if data:
                m = data[0]
                print(f"Sample - Question: {m.get('question')[:50]}...")
                print(f"Sample - Category: {m.get('category')}")
                print(f"Sample - OutcomePrices: {m.get('outcomePrices')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_data_api_leaderboard():
    print("\n--- Testing Data API (Leaderboard) ---")
    try:
        url = f"{DATA_API}/leaderboard?category=OVERALL&orderBy=PNL&limit=5"
        response = requests.get(url, timeout=15)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            traders = []
            if isinstance(data, list):
                traders = data
            elif isinstance(data, dict):
                traders = data.get("data", data.get("traders", []))
            
            print(f"Traders found: {len(traders)}")
            if traders:
                t = traders[0]
                print(f"Sample Trader: {t.get('userName') or t.get('address')}")
                print(f"Sample PnL: {t.get('pnl') or t.get('profit')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_coingecko_api():
    print("\n--- Testing CoinGecko API ---")
    try:
        url = f"{COINGECKO_API}/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true"
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Data keys: {list(data.keys())}")
            for coin in ["bitcoin", "ethereum", "solana"]:
                if coin in data:
                    print(f"{coin.capitalize()} 24h change: {data[coin].get('usd_24h_change')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_gamma_api()
    test_data_api_leaderboard()
    test_coingecko_api()
