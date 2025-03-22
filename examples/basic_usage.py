#!/usr/bin/env python
"""
Basic usage example for the Questrade Custom API Wrapper
"""

import os
from QuestradeAPI import QuestradeAPI

def main():
    """
    Demonstrates basic usage of the Questrade API wrapper.
    """
    # You can provide a refresh token directly or store it in a file
    refresh_token = os.environ.get('QUESTRADE_REFRESH_TOKEN')
    
    # Initialize the API with the refresh token
    api = QuestradeAPI(refresh_token=refresh_token)
    
    # Get account information
    accounts = api.get_accounts()
    print(f"Found {len(accounts['accounts'])} accounts:")
    
    for account in accounts['accounts']:
        print(f"  - {account['type']} ({account['number']})")
        
        # Get account positions
        positions = api.get_account_positions(account['number'])
        print(f"    Positions: {len(positions['positions'])}")
        
        # Get account balances
        balances = api.get_account_balances(account['number'])
        print(f"    CAD Balance: {balances['perCurrencyBalances'][0]['cash']}")
        
    # Search for a symbol
    search_results = api.search_symbols("AAPL")
    print(f"\nSearch results for 'AAPL': {len(search_results['symbols'])}")
    
    if search_results['symbols']:
        symbol = search_results['symbols'][0]
        symbol_id = symbol['symbolId']
        print(f"  Symbol ID for {symbol['symbol']}: {symbol_id}")
        
        # Get quote for the symbol
        quote = api.get_quote(symbol_id)
        print(f"  Current price: ${quote['quotes'][0]['lastTradePrice']}")
        
        # Get candles for the symbol
        candles = api.get_candles(
            symbol_id=symbol_id,
            start_time="2023-01-01T00:00:00-05:00",
            end_time="2023-01-31T00:00:00-05:00",
            interval="OneDay"
        )
        print(f"  Candles: {len(candles['candles'])}")
        print(f"  First candle: {candles['candles'][0]['start']} - Open: ${candles['candles'][0]['open']}, Close: ${candles['candles'][0]['close']}")

if __name__ == "__main__":
    main() 