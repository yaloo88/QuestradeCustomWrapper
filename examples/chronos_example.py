#!/usr/bin/env python
"""
Example usage of the Chronos class for efficiently retrieving and caching market data
"""

import os
import pandas as pd
from pathlib import Path
from QuestradeAPI import QuestradeAPI, Chronos

def main():
    """
    Demonstrates how to use the Chronos class to fetch and cache market data.
    
    The Chronos class provides an efficient way to work with historical market data by:
    1. Caching symbol information in a local SQLite database
    2. Storing candle data to minimize API calls
    3. Smart updating of data by only fetching what's needed
    """
    # Get refresh token from environment (you can replace with your method)
    refresh_token = os.environ.get('QUESTRADE_REFRESH_TOKEN')
    
    # Initialize the Questrade API
    api = QuestradeAPI(refresh_token=refresh_token)
    
    # Initialize Chronos using the existing API instance
    chronos = Chronos(api=api)
    
    # Example 1: Get symbol information
    # This will fetch from the API only if the symbol isn't already in the database
    print("\n=== Example 1: Get Symbol Information ===")
    apple_info = chronos.get_symbol_info("AAPL")
    print(f"Symbol ID for AAPL: {apple_info['symbolId']}")
    print(f"Description: {apple_info['description']}")
    print(f"Security Type: {apple_info['securityType']}")
    
    # Example 2: Get historical candles
    # Using a shorter timeframe for the example
    print("\n=== Example 2: Get Minute Candles (First Run) ===")
    # First time fetch (or if database is empty for this symbol/timeframe)
    candles_df = chronos.get_candles(symbol="AAPL", days=5, interval="OneMinute")
    print(f"Retrieved {len(candles_df)} candles for AAPL")
    if not candles_df.empty:
        print("\nSample data:")
        print(candles_df.head())
    
    # Example 3: Call again to demonstrate caching
    print("\n=== Example 3: Get Minute Candles (Second Run - Should be from cache) ===")
    # Second run should be much faster, as it will use cached data
    candles_df2 = chronos.get_candles(symbol="AAPL", days=5, interval="OneMinute")
    print(f"Retrieved {len(candles_df2)} candles for AAPL from cache")
    
    # Example 4: Force refresh to demonstrate API update
    print("\n=== Example 4: Force refresh to demonstrate API update ===")
    candles_df3 = chronos.get_candles(
        symbol="AAPL", 
        days=5, 
        interval="OneMinute", 
        force_refresh=True
    )
    print(f"Retrieved {len(candles_df3)} candles for AAPL after forced refresh")
    
    # Example 5: Get candles for a different symbol and timeframe
    print("\n=== Example 5: Get Daily Candles for a Different Symbol ===")
    msft_daily = chronos.get_candles(symbol="MSFT", days=30, interval="OneDay")
    print(f"Retrieved {len(msft_daily)} daily candles for MSFT")
    if not msft_daily.empty:
        print("\nMSFT daily candles sample:")
        print(msft_daily.head())
    
    # Check the location of the SQLite databases
    data_dir = chronos.project_root / "data"
    print(f"\nData is stored in: {data_dir}")
    print("Database files:")
    for file in data_dir.glob("*.db"):
        print(f"- {file.name}")

if __name__ == "__main__":
    main() 