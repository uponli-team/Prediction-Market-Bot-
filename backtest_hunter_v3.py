"""
PolyGranted Scout - Divergence Hunter v3 Backtester
Simulates performance of AI vs Human divergence strategy using Monte Carlo.
"""
import random
import pandas as pd
import numpy as np

def run_v3_backtest(n_simulations=5000, min_edge=0.065, capital=10000):
    print(f"📈 PolyGranted Scout - Divergence Hunter v3 Backtest")
    print(f"Simulating {n_simulations} high-conviction signals...")
    print(f"Initial Capital: ${capital:,.2f} | Min Edge: {min_edge*100}%")
    print("-" * 50)

    results = []
    current_balance = capital
    
    # Strategy Assumptions based on Hunter v3 logic
    # 1. AI Accuracy: High-edge signals generally have higher predictive power.
    # We'll assume a 'Base Win Rate' and an 'Edge Alpha'.
    base_win_rate = 0.52 # Better than coin flip
    edge_alpha = 0.45    # How much of the 'edge' translates to real win probability beyond base

    for i in range(n_simulations):
        # 1. Generate a realistic signal
        # Markets are usually between 10% and 90%
        implied_odds = random.uniform(0.10, 0.90)
        
        # Divergence Hunter v3 finding an edge (Gaussian distribution centered on 8%)
        found_edge = np.random.normal(0.08, 0.03) 
        if found_edge < min_edge: continue # Strategy skip
        
        # AI prediction
        ai_consensus = min(0.98, max(0.02, implied_odds + found_edge))
        edge = ai_consensus - implied_odds
        
        # 2. Probability of winning (The "Secret Sauce")
        # True Win Prob = Implied + (Found Edge * Hunter Confidence Factor)
        true_win_prob = implied_odds + (edge * (base_win_rate + edge_alpha))
        true_win_prob = min(0.99, max(0.01, true_win_prob))
        
        # 3. Betting Strategy (Fixed bet for realism)
        bet_amount = 100 # $100 per trade
        
        # 4. Outcome Simulation
        win = random.random() < true_win_prob
        
        # PnL Calculation
        # ROI if win = (1 / implied_odds) - 1
        if win:
            pnl = bet_amount * ((1.0 / implied_odds) - 1.0)
        else:
            pnl = -bet_amount
            
        current_balance += pnl
        
        results.append({
            "trade": i,
            "implied": implied_odds * 100,
            "ai": ai_consensus * 100,
            "edge": edge * 100,
            "win": win,
            "pnl": pnl,
            "balance": current_balance
        })

    df = pd.DataFrame(results)
    
    if df.empty:
        print("No trades met the criteria during simulation.")
        return

    # Summary Stats
    total_trades = len(df)
    net_pnl = df['pnl'].sum()
    win_rate = df['win'].mean()
    max_drawdown = (df['balance'].cummax() - df['balance']).max()
    final_balance = df['balance'].iloc[-1]
    roi = (final_balance - capital) / capital * 100

    print(f"Total Trades Taken: {total_trades}")
    print(f"Win Rate: {win_rate*100:.1f}%")
    print(f"Final Balance: ${final_balance:,.2f}")
    print(f"Total ROI: {roi:+.2f}%")
    print(f"Max Drawdown: ${max_drawdown:,.2f}")
    print(f"Average PnL per Trade: ${df['pnl'].mean():.2f}")
    print("-" * 50)
    
    # Tiered Analysis (High Edge vs Low Edge)
    df['edge_tier'] = pd.cut(df['edge'], bins=[6.5, 10, 15, 100], labels=['6.5-10%', '10-15%', '15%+'])
    tier_summary = df.groupby('edge_tier', observed=False)['pnl'].agg(['count', 'sum', 'mean'])
    print("\nPerformance by Edge Intensity:")
    print(tier_summary)

if __name__ == "__main__":
    run_v3_backtest()
