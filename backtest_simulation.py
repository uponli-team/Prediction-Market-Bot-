import random
import pandas as pd

def simulate_strategy(n_markets=10000, granted_edge=0.065, prospect_edge=0.03):
    print(f"📊 Running Strategy Simulation ({n_markets} markets)...")
    print(f"Rules: Granted >= {granted_edge*100}%, Prospect >= {prospect_edge*100}%")
    
    results = []
    
    for _ in range(n_markets):
        # 1. Market setup
        implied_prob = random.uniform(0.10, 0.90)
        
        # 2. Simulated High Volatility Factors
        cg_momentum = random.uniform(-15.0, 15.0)  # Up to 15% price swing
        binance_funding = random.uniform(-0.5, 0.5) # High leverage sentiment
        llama_tvl = random.uniform(-10.0, 10.0) # Major TVL flows
        
        # 3. Apply Bot's Prediction Logic (Weighted for more sensitivity in simulation)
        # Using a Multiplier to simulate 'high-conviction' scenarios
        bias = (cg_momentum / 10.0) * 0.05  # Increased sensitivity to 5% per 10% move
        bias += (binance_funding * 0.03)     # Increased leverage weight
        bias += (llama_tvl / 100.0) * 0.04   # Increased TVL weight
        
        predicted_prob = min(0.99, max(0.01, implied_prob + bias))
        
        edge_yes = predicted_prob - implied_prob
        edge_no = implied_prob - predicted_prob
        
        best_edge = max(edge_yes, edge_no)
        decision = "YES" if edge_yes > edge_no else "NO"
        
        # 4. Determine Tier
        tier = "NONE"
        if best_edge >= granted_edge:
            tier = "GRANTED"
        elif best_edge >= prospect_edge:
            tier = "PROSPECT"
            
        if tier == "NONE":
            continue
            
        # 5. Reality Check (The "Alpha")
        # We simulate if our 'bias' actually has predictive power.
        # If our bias is +2%, let's say the 'True Prob' is Implied + (Bias * AlphaFactor)
        # We'll assume the strategy has a 60% 'Edge Accuracy'
        alpha_factor = 1.2 # The strategy is slightly BETTER than its own bias estimation
        true_prob = min(1.0, max(0.0, implied_prob + (bias * alpha_factor)))
        
        win = random.random() < (true_prob if decision == "YES" else (1.0 - true_prob))
        
        # 6. PnL (Simplified: $100 bet, payout is 1/price)
        # Cost is 'implied_prob' dollars for 1 share that pays $1.00
        cost = implied_prob if decision == "YES" else (1.0 - implied_prob)
        pnl = 1.0 - cost if win else -cost
        
        results.append({
            "tier": tier,
            "edge": best_edge,
            "win": win,
            "pnl": pnl * 100 # Scaled to $100 per share
        })
        
    df = pd.DataFrame(results)
    
    if df.empty:
        print("❌ No trades triggered with these settings.")
        return

    summary = df.groupby("tier").agg({
        "pnl": ["count", "sum", "mean"],
        "win": "mean"
    })
    
    print("\n" + "="*40)
    print("      BACKTEST RESULTS SUMMARY")
    print("="*40)
    print(summary)
    print("="*40)
    print(f"Total Net PnL: ${df['pnl'].sum():.2f}")
    print(f"Overall Win Rate: {df['win'].mean()*100:.1f}%")
    print("="*40)

if __name__ == "__main__":
    simulate_strategy()
