#!/usr/bin/env python
"""
Questrade API Examples

This script provides examples of how to use all of the methods in the
Questrade API wrapper. Each example is self-contained and shows both the
method call and how to access the returned data.
"""

import os
import sys
from pathlib import Path
import datetime
import json
from pprint import pprint
import time
from QuestradeAPI.CustomWrapper import QuestradeAPI, QuestradeAPIError, QuestradeRateLimitError

# Add project root to path
project_root = Path(__file__).parent.parent.resolve()
sys.path.append(str(project_root))

def print_section(title):
    """Print a section title."""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80 + "\n")

def print_result(name, result, truncate=True):
    """Print a result with formatting."""
    print(f"\n--- {name} ---")
    
    if isinstance(result, dict) and truncate:
        # Only print the first few items of each dictionary to keep output clean
        truncated_result = {}
        for key, value in result.items():
            if isinstance(value, list) and len(value) > 2:
                truncated_result[key] = value[:2] + ["..."]
            else:
                truncated_result[key] = value
        pprint(truncated_result)
    else:
        pprint(result)
    print()

def run_examples():
    """Run examples of QuestradeAPI usage."""
    print("Starting Questrade API examples...\n")
    
    # Initialize API
    api = QuestradeAPI()
    
    try:
        # Authentication example
        print("\n=== Authentication ===")
        api.authenticate()
        print("Successfully authenticated with the Questrade API.")
        
        # Demonstrate rate limiting
        print("\n=== Rate Limiting Example ===")
        demonstrate_rate_limiting(api)
        
        # Time endpoint example
        print("\n=== Time Endpoint ===")
        time_response = api.get_time()
        print(f"Current server time: {time_response.get('time')}")
        
        # Account endpoints examples
        print("\n=== Account Endpoints ===")
        accounts_response = api.get_accounts()
        print(f"Retrieved {len(accounts_response.get('accounts', []))} accounts:")
        for account in accounts_response.get('accounts', []):
            print(f"  - {account.get('type')} account (ID: {account.get('number')}) - Status: {account.get('status')}")
        
        if len(accounts_response.get('accounts', [])) > 0:
            account_id = accounts_response['accounts'][0]['number']
            print(f"\nUsing account ID: {account_id} for examples\n")
            
            # Get account balances
            balances = api.get_account_balances(account_id)
            print("Account balances:")
            for currency_group in balances.get('perCurrencyBalances', []):
                currency = currency_group.get('currency', 'Unknown')
                print(f"  {currency}:")
                print(f"    - Buying Power: {currency_group.get('buyingPower', 'N/A')}")
                print(f"    - Cash: {currency_group.get('cash', 'N/A')}")
                print(f"    - Total Equity: {currency_group.get('totalEquity', 'N/A')}")
            
            # Get account positions
            positions = api.get_account_positions(account_id)
            print("\nAccount positions:")
            if positions.get('positions', []):
                for position in positions.get('positions', []):
                    print(f"  - {position.get('symbol', 'Unknown')}: {position.get('openQuantity', 0)} shares")
            else:
                print("  No positions found")
            
            # Get account activities
            end_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
            start_time = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
            activities = api.get_account_activities(account_id, start_time=start_time, end_time=end_time)
            print(f"\nAccount activities for the last 10 days:")
            if activities.get('activities', []):
                for activity in activities.get('activities', [])[:5]:  # Show first 5 activities
                    print(f"  - {activity.get('type', 'Unknown')}: {activity.get('description', 'No description')} ({activity.get('tradeDate', 'Unknown date')})")
                if len(activities.get('activities', [])) > 5:
                    print(f"  ... and {len(activities.get('activities', [])) - 5} more")
            else:
                print("  No activities found")
            
            # Get account orders
            orders = api.get_account_orders(account_id)
            print("\nAccount orders:")
            if orders.get('orders', []):
                for order in orders.get('orders', [])[:5]:  # Show first 5 orders
                    print(f"  - {order.get('symbol', 'Unknown')}: {order.get('side', 'Unknown')} {order.get('quantity', 0)} @ {order.get('limitPrice', 'Market')} ({order.get('state', 'Unknown state')})")
                if len(orders.get('orders', [])) > 5:
                    print(f"  ... and {len(orders.get('orders', [])) - 5} more")
            else:
                print("  No orders found")
            
            # Get account executions
            executions = api.get_account_executions(account_id)
            print("\nAccount executions:")
            if executions.get('executions', []):
                for execution in executions.get('executions', [])[:5]:  # Show first 5 executions
                    print(f"  - {execution.get('symbol', 'Unknown')}: {execution.get('side', 'Unknown')} {execution.get('quantity', 0)} @ {execution.get('price', 'Unknown')} ({execution.get('orderId', 'Unknown order')})")
                if len(executions.get('executions', [])) > 5:
                    print(f"  ... and {len(executions.get('executions', [])) - 5} more")
            else:
                print("  No executions found")
        
        # Market endpoints examples
        print("\n=== Market Endpoints ===")
        markets = api.get_markets()
        print(f"Retrieved {len(markets.get('markets', []))} markets:")
        for market in markets.get('markets', [])[:3]:  # Show first 3 markets
            print(f"  - {market.get('name', 'Unknown')} (ID: {market.get('marketId', 'Unknown')})")
            print(f"    - Trading: {market.get('tradingVenues', [])}")
            print(f"    - Extended Hours: {market.get('extendedStartTime', 'N/A')} - {market.get('extendedEndTime', 'N/A')}")
            print(f"    - Regular Hours: {market.get('startTime', 'N/A')} - {market.get('endTime', 'N/A')}")
        
        # Symbol endpoints examples
        print("\n=== Symbol Endpoints ===")
        search_results = api.search_symbols("AAPL")
        print("Search results for 'AAPL':")
        for symbol in search_results.get('symbols', []):
            print(f"  - {symbol.get('symbol', 'Unknown')} ({symbol.get('description', 'No description')}) on {symbol.get('listingExchange', 'Unknown exchange')}")
        
        if search_results.get('symbols', []):
            symbol_id = search_results['symbols'][0]['symbolId']
            symbol_name = search_results['symbols'][0]['symbol']
            print(f"\nUsing symbol: {symbol_name} (ID: {symbol_id}) for examples\n")
            
            # Get symbol details
            symbol_details = api.get_symbol(symbol_id)
            print(f"Symbol details for {symbol_name}:")
            if 'symbols' in symbol_details and symbol_details['symbols']:
                details = symbol_details['symbols'][0]
                print(f"  - Description: {details.get('description', 'N/A')}")
                print(f"  - Currency: {details.get('currency', 'N/A')}")
                print(f"  - Market Cap: {details.get('marketCap', 'N/A')}")
                print(f"  - PE Ratio: {details.get('pe', 'N/A')}")
                print(f"  - EPS: {details.get('eps', 'N/A')}")
                print(f"  - Dividend: {details.get('dividend', 'N/A')} ({details.get('yield', 'N/A')}%)")
            
            # Get symbol options
            options = api.get_symbol_options(symbol_id)
            print(f"\nOptions chain for {symbol_name}:")
            if 'options' in options and options['options']:
                for expiry_date in options['options'][:2]:  # Show first 2 expiry dates
                    print(f"  Expiry: {expiry_date.get('expiryDate', 'Unknown')}")
                    if 'chainPerRoot' in expiry_date and expiry_date['chainPerRoot']:
                        for root in expiry_date['chainPerRoot'][:1]:  # Show first root
                            if 'chainPerStrikePrice' in root and root['chainPerStrikePrice']:
                                for strike in root['chainPerStrikePrice'][:3]:  # Show first 3 strikes
                                    print(f"    Strike: ${strike.get('strikePrice', 'Unknown')}")
                                    if 'callSymbolId' in strike:
                                        print(f"      Call: {strike.get('callSymbolId', 'N/A')}")
                                    if 'putSymbolId' in strike:
                                        print(f"      Put: {strike.get('putSymbolId', 'N/A')}")
                                if len(root['chainPerStrikePrice']) > 3:
                                    print(f"      ... and {len(root['chainPerStrikePrice']) - 3} more strikes")
            else:
                print("  No options found")
            
            # Get quote
            quote = api.get_quote(symbol_id)
            print(f"\nQuote for {symbol_name}:")
            if 'quotes' in quote and quote['quotes']:
                q = quote['quotes'][0]
                print(f"  - Bid: ${q.get('bidPrice', 'N/A')} ({q.get('bidSize', 'N/A')})")
                print(f"  - Ask: ${q.get('askPrice', 'N/A')} ({q.get('askSize', 'N/A')})")
                print(f"  - Last: ${q.get('lastTradePrice', 'N/A')} ({q.get('lastTradeSize', 'N/A')})")
                print(f"  - Volume: {q.get('volume', 'N/A')}")
                print(f"  - VWAP: ${q.get('VWAP', 'N/A')}")
            
            # Get candles
            end_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
            start_time = (datetime.datetime.now() - datetime.timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
            candles = api.get_candles(symbol_id, start_time, end_time, interval='OneDay')
            print(f"\nLast 5 days of daily candles for {symbol_name}:")
            if 'candles' in candles and candles['candles']:
                for candle in candles['candles']:
                    print(f"  - {candle.get('start', 'Unknown')}: Open ${candle.get('open', 'N/A')}, Close ${candle.get('close', 'N/A')}, High ${candle.get('high', 'N/A')}, Low ${candle.get('low', 'N/A')}, Vol {candle.get('volume', 'N/A')}")
            else:
                print("  No candles found")
        
        # Get multiple symbols at once
        symbols = api.get_symbols(symbol_names=["AAPL", "MSFT"])
        print(f"\nRetrieved {len(symbols.get('symbols', []))} symbols by name:")
        for symbol in symbols.get('symbols', []):
            print(f"  - {symbol.get('symbol', 'Unknown')} ({symbol.get('description', 'No description')}) on {symbol.get('listingExchange', 'Unknown exchange')}")
        
        # Example complete
        print("\nAll examples completed successfully.")

    except QuestradeAPIError as e:
        print(f"API Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

def demonstrate_rate_limiting(api):
    """Demonstrate the rate limiting functionality."""
    # Save original settings
    original_enforce_rate_limit = api.enforce_rate_limit
    original_max_retries = api.max_retries
    original_retry_wait = api.retry_wait_time
    
    try:
        # Configure API for demonstration
        api.enforce_rate_limit = True
        api.max_retries = 3
        api.retry_wait_time = 1  # Short wait time for demo
        
        print("1. Making a series of rapid requests to demonstrate rate limiting:")
        
        # Make a series of requests to demonstrate rate limiting
        for i in range(5):
            try:
                # Get the time endpoint multiple times in quick succession
                start = time.time()
                response = api.get_time()
                elapsed = time.time() - start
                print(f"   Request {i+1}: Successful in {elapsed:.2f}s - Server time: {response.get('time')}")
                time.sleep(0.1)  # Small delay between requests for this example
            except QuestradeRateLimitError as e:
                print(f"   Request {i+1}: Rate limit exceeded! {e}")
                break
        
        print("\n2. Simulating a rate limit error by manipulating the rate limiter:")
        
        # Artificially fill the rate limiter to simulate hitting the limit
        category = api.rate_limiter.get_category_for_endpoint('v1/time')
        for _ in range(api.rate_limiter.RATE_LIMITS[category][0]):
            api.rate_limiter.record_request(category)
        
        # Now attempt a request which should hit the limit and retry
        api.max_retries = 0  # Set to 0 to show the error
        try:
            response = api.get_time()
            print("   Unexpected success - rate limiting failed to trigger")
        except QuestradeRateLimitError as e:
            print(f"   Expected rate limit error: {e}")
        
        print("\n3. Demonstrating automatic retry functionality:")
        
        # Enable retries
        api.max_retries = 2
        api.retry_wait_time = 2
        
        # Fill the rate limiter again
        for _ in range(api.rate_limiter.RATE_LIMITS[category][0]):
            api.rate_limiter.record_request(category)
        
        # With retries enabled, this should eventually succeed after waiting
        try:
            start = time.time()
            response = api.get_time()
            elapsed = time.time() - start
            print(f"   Request succeeded after {elapsed:.2f}s with automatic retries")
            print(f"   Server time: {response.get('time')}")
        except QuestradeRateLimitError as e:
            print(f"   Rate limit error even with retries: {e}")
            
        print("\n4. Turning off rate limiting for comparison:")
        
        # Disable rate limiting
        api.enforce_rate_limit = False
        
        # Make rapid requests without rate limiting
        for i in range(3):
            try:
                start = time.time()
                response = api.get_time()
                elapsed = time.time() - start
                print(f"   Request {i+1}: Completed in {elapsed:.2f}s with rate limiting disabled")
                time.sleep(0.1)  # Small delay between requests for this example
            except Exception as e:
                print(f"   Request {i+1} failed: {e}")
    
    finally:
        # Restore original settings
        api.enforce_rate_limit = original_enforce_rate_limit
        api.max_retries = original_max_retries
        api.retry_wait_time = original_retry_wait
        
        # Clear rate limiter history
        api.rate_limiter.reset()
        
        print("\nRate limiting example complete")

if __name__ == "__main__":
    run_examples() 