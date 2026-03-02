import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GAMMA_API = "https://gamma-api.polymarket.com"

def fetch_closed_markets(limit=20):
    try:
        url = f"{GAMMA_API}/markets?closed=true&limit={limit}"
        print(f"Fetching: {url}")
        response = requests.get(url, timeout=20)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        return data
    except Exception as e:
        print(f"Error: {e}")
        return []

def backtest():
    print("🚀 Starting Backtest on Closed Polymarket Data...")
    closed_markets = fetch_closed_markets(100)
    print(f"Found {len(closed_markets)} closed markets.")
    
    # We will simulate the strategy on these markets
    # Note: For closed markets, outcomePrices usually shows the final state (0 or 1)
    # We need to see if we can get the 'implied probability' from a time BEFORE it closed.
    # In some API responses, there's a 'lastTradePrice' or similar.
    
    for market in closed_markets[:5]:
        print(f"\nMarket: {market.get('question')}")
        print(f"Slug: {market.get('slug')}")
        print(f"Outcome: {market.get('outcomePrices')}")

if __name__ == "__main__":
    backtest()
