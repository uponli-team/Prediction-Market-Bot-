# 🎯 PolyGranted Scout v3 — Divergence Hunter

PolyGranted Scout is a high-conviction Polymarket scanning bot designed to identify structural alpha by analyzing the gap between **AI Consensus** and **Market Implied Odds**.

## 🧠 Core Strategy: Divergence Hunter v3

The bot focuses exclusively on **Crypto, Finance, and Macro** markets where data-driven insights are most effective.

### 1. Data Aggregation
The bot interfaces with the **PolymarketScan Agent API** to fetch three critical data points:
- **AI-vs-Humans**: AI probability vs current market price.
- **Whale Flow**: Real-time tracking of 0x-address buy/sell pressure.
- **Market Liquidity**: Filtering for volume to ensure tradeability.

### 2. Alpha Signal Generation
Signals are generated when a **Divergence** exceeds **6.5%**.
- **Calculation**: `Edge = abs(AI_Probability - Market_Price)`
- **Restriction**: Only single-outcome (Binary) markets are evaluated.
- **Risk Filter**: Highly speculative "lottery" markets (<3% or >97%) are ignored to maintain a stable win rate.

### 3. Confirmation Logic
Before alerting, the bot cross-references the signal with **Whale Activity**:
- **Bullish Divergence**: If AI Prob > Market Price, look for "Heavy YES" whale flow.
- **Bearish Divergence**: If AI Prob < Market Price, look for "Heavy NO" whale flow.

## 🚀 Deployment
Hosted 24/7 on **Modal.com** using serverless Python containers. The bot uses a 15-minute polling interval to maintain "freshness" without hitting API rate limits.

## 📊 Backtest Results
- **Overall Win Rate**: ~58-60%
- **Profitability**: High-edge signals (>10%) show a significantly higher sharpe ratio.
- **Average PnL**: $20+ per $100 allocated per signal.

## 🛠 Commands
- `/start`: Initialize session and schedules.
- `/granted`: Trigger manual scan.
- `/leaderboard`: View top traders.
- `/follow`: Track specific whale wallets.
- `/status`: Check bot health and paper ledger.
