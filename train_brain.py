import yfinance as yf
import pandas as pd
import numpy as np
import json

# --- CONFIGURATION ---
# Define the assets and the parameters we want to test across history
TICKERS = {
    "cement": "ULTRACEMCO.NS",
    "infra": "LT.NS",
    "steel": "TATASTEEL.NS"
}

# The grid of combinations to check across history
LOOKBACK_OPTIONS = [5, 10, 15, 20, 30, 40, 60]
THRESHOLD_OPTIONS = [0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05]

def backtest_strategy(df, lookback, threshold):
    """
    Simulates the historical returns for a specific lookback/threshold mix.
    """
    df = df.copy()
    
    # Calculate historical rolling returns
    df['rolling_ret'] = df['Close'].pct_change(periods=lookback)
    
    # Generate long (1) or neutral (0) trading signals based on breakout threshold
    df['signal'] = np.where(df['rolling_ret'] > threshold, 1, 0)
    
    # Shift signals by 1 day to simulate executing the trade the following day
    df['strategy_ret'] = df['signal'].shift(1) * df['Close'].pct_change()
    
    # Compute total cumulative compounding return factor
    cumulative_return = (1 + df['strategy_ret'].fillna(0)).prod()
    return cumulative_return

def main():
    print("⏳ Stage 1: Downloading max historical data frames...")
    # Fetching parallel historical structures using threads
    raw_data = yf.download(list(TICKERS.values()), period="max", group_by='ticker', threads=True)
    
    brain_rules = {}
    
    print("⏳ Stage 2: Commencing 50-year parameter matrix sweep...")
    for sector, ticker in TICKERS.items():
        print(f"👉 Analyzing {sector.upper()} ({ticker})...")
        
        # Extract individual ticker dataframe columns safely
        if ticker in raw_data.columns.levels[0]:
            df = raw_data[ticker].dropna(subset=['Close'])
        else:
            # Fallback if download grouping returns standard index layout
            df = raw_data.copy()
            
        best_return = 0.0
        best_lookback = 20
        best_threshold = 0.03
        
        # Loop through all grid parameter iterations to locate the optimal historical peak
        for lookback in LOOKBACK_OPTIONS:
            for threshold in THRESHROW_OPTIONS if 'THRESHOLD_OPTIONS' in locals() else THRESHOLD_OPTIONS:
                final_equity_factor = backtest_strategy(df, lookback, threshold)
                
                if final_equity_factor > best_return:
                    best_return = final_equity_factor
                    best_lookback = lookback
                    best_threshold = threshold
                    
        print(f"✅ Optimal match found! Lookback: {best_lookback}d, Threshold: {best_threshold*100}%, Peak Return Factor: {best_return:.2f}x")
        
        # Save the winning parameters into our brain structure matrix
        brain_rules[f"{sector}_optimal_lookback"] = best_lookback
        brain_rules[f"{sector}_optimal_threshold"] = best_threshold

    # --- STAGE 3: SAVE RULEBOOK ---
    print("⏳ Stage 3: Writing rulebook matrix payload to repository state...")
    with open("factory_state/brain_rules.json", "w") as f:
        json.dump(brain_rules, f, indent=4)
        
    print("🚀 Process complete! factory_state/brain_rules.json generated successfully.")

if __name__ == "__main__":
    main()