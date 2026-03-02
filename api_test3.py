import requests
cid = "0xe3b423dfad8c22ff75c9899c4e8176f628cf4ad4caa00481764d320e7415f7a9"
p = requests.get(f"https://clob.polymarket.com/prices?market={cid}")
print(p.status_code, p.text[:100])
