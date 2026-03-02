import asyncio
from bot import scan_markets

async def test():
    try:
        results = scan_markets()
        print(f"Results: {results}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
