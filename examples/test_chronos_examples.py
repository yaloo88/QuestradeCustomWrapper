#!/usr/bin/env python
"""
Test script to verify Chronos implementation against examples from the notebook.
This script ensures Chronos has all the methods and functionality shown in the examples.
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import sqlite3
from pathlib import Path

try:
    from QuestradeAPI import QuestradeAPI, Chronos
    print("Successfully imported QuestradeAPI and Chronos")
except ImportError as e:
    print(f"Error importing QuestradeAPI modules: {e}")
    print("Make sure you're running this script from the project root directory")
    exit(1)

def verify_chronos_attributes():
    """
    Verify that Chronos has all the required attributes and methods
    from the examples in the notebook.
    """
    print("\n=== Verifying Chronos Attributes and Methods ===")
    
    # Initialize Chronos
    api = QuestradeAPI()
    chronos = Chronos(api=api)
    
    # Check required attributes
    required_attributes = [
        'api', 'project_root', 'db_path', 'conn', 'symbol_cache'
    ]
    
    # Check required methods
    required_methods = [
        '_ensure_db_connection', '_db_to_api_format', '_api_to_db_format',
        'get_symbol_info', 'get_all_symbols', 'bulk_insert_symbols',
        'update_stale_symbols', 'search_symbols_in_db', 'get_db_stats',
        'optimize_db', 'clear_symbol_cache', '__del__',
        'get_candles', 'get_updated_candles', 'search_candles_from_db'
    ]
    
    # Verify attributes
    print("\nChecking required attributes:")
    for attr in required_attributes:
        if hasattr(chronos, attr):
            print(f"✓ {attr}")
        else:
            print(f"✗ {attr} - MISSING")
    
    # Verify methods
    print("\nChecking required methods:")
    for method in required_methods:
        if hasattr(chronos, method) and callable(getattr(chronos, method)):
            print(f"✓ {method}")
        else:
            print(f"✗ {method} - MISSING")
    
    return chronos, api

def test_get_symbol_info(chronos):
    """Test the get_symbol_info method as shown in the examples."""
    print("\n=== Testing get_symbol_info Method ===")
    
    symbol = input("Enter a symbol to look up (default: AAPL): ").strip().upper() or "AAPL"
    
    try:
        # First call should fetch from API
        print(f"\nLooking up {symbol} (first call, may fetch from API):")
        symbol_info = chronos.get_symbol_info(symbol_name=symbol)
        print(f"Retrieved symbol info for {symbol}:")
        for key, value in symbol_info.items():
            print(f"  {key}: {value}")
        
        # Second call should use cache
        print(f"\nLooking up {symbol} again (should use cache):")
        symbol_info2 = chronos.get_symbol_info(symbol_name=symbol)
        print(f"Retrieved from cache: {'Symbol cache hit' in str(sys.stdout)}")
        
        # Test symbol caching
        if symbol in chronos.symbol_cache:
            print("✓ Symbol correctly stored in cache")
        else:
            print("✗ Symbol not found in cache")
            
        return symbol, symbol_info
    except Exception as e:
        print(f"Error in get_symbol_info: {e}")
        return None, None

def test_get_candles(chronos, symbol):
    """Test the get_candles method as shown in the examples."""
    if not symbol:
        print("No symbol provided, skipping get_candles test")
        return
        
    print(f"\n=== Testing get_candles Method for {symbol} ===")
    
    try:
        # Test with default parameters
        print("\nTesting with default parameters (30 days, OneMinute):")
        candles_df = chronos.get_candles(symbol=symbol)
        print(f"Retrieved {len(candles_df)} candles")
        if not candles_df.empty:
            print("DataFrame columns:", candles_df.columns.tolist())
            print("Sample data:")
            print(candles_df.head(3))
        
        # Test with custom parameters
        print("\nTesting with custom parameters (5 days, OneDay):")
        candles_df2 = chronos.get_candles(symbol=symbol, days=5, interval="OneDay")
        print(f"Retrieved {len(candles_df2)} daily candles")
        if not candles_df2.empty:
            print("Sample data:")
            print(candles_df2.head(3))
        
        # Verify that returned object is a pandas DataFrame
        if isinstance(candles_df, pd.DataFrame):
            print("✓ Return value is a pandas DataFrame as expected")
        else:
            print(f"✗ Return value is {type(candles_df)}, not a pandas DataFrame")
            
        # Verify expected columns
        expected_columns = ['start', 'end', 'low', 'high', 'open', 'close', 'volume']
        missing_columns = [col for col in expected_columns if col not in candles_df.columns]
        if not missing_columns:
            print("✓ DataFrame contains all expected columns")
        else:
            print(f"✗ Missing expected columns: {missing_columns}")
    
    except Exception as e:
        print(f"Error in get_candles: {e}")

def test_get_updated_candles(chronos, symbol):
    """Test the get_updated_candles method as shown in the examples."""
    if not symbol:
        print("No symbol provided, skipping get_updated_candles test")
        return
        
    print(f"\n=== Testing get_updated_candles Method for {symbol} ===")
    
    try:
        # Test get_updated_candles
        print("\nCalling get_updated_candles:")
        candles = chronos.get_updated_candles(symbol=symbol, interval="OneDay")
        
        # Verify structure
        if isinstance(candles, dict) and 'candles' in candles:
            print(f"✓ Return value is a dict with 'candles' key as expected")
            print(f"Retrieved {len(candles['candles'])} candles")
            
            # Check first candle
            if candles['candles']:
                first_candle = candles['candles'][0]
                print("\nFirst candle structure:")
                for key, value in first_candle.items():
                    print(f"  {key}: {value}")
                
                # Check expected keys
                expected_keys = ['start', 'end', 'low', 'high', 'open', 'close', 'volume']
                missing_keys = [key for key in expected_keys if key not in first_candle]
                if not missing_keys:
                    print("✓ Candle contains all expected fields")
                else:
                    print(f"✗ Missing expected fields: {missing_keys}")
        else:
            print(f"✗ Return value is {type(candles)}, not a dict with 'candles' key")
    
    except Exception as e:
        print(f"Error in get_updated_candles: {e}")

def test_search_candles_from_db(chronos, symbol):
    """Test the search_candles_from_db method as shown in the examples."""
    if not symbol:
        print("No symbol provided, skipping search_candles_from_db test")
        return
        
    print(f"\n=== Testing search_candles_from_db Method for {symbol} ===")
    
    try:
        # Get a date range
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        
        print(f"\nSearching for candles between {start_date} and {end_date}:")
        candles = chronos.search_candles_from_db(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval="OneDay"
        )
        
        # Verify structure
        if isinstance(candles, dict) and 'candles' in candles:
            print(f"✓ Return value is a dict with 'candles' key as expected")
            print(f"Found {len(candles['candles'])} candles in the date range")
            
            # Check candle structure if any found
            if candles['candles']:
                print("\nSample candle structure:")
                for key, value in candles['candles'][0].items():
                    print(f"  {key}: {value}")
        else:
            print(f"✗ Return value is {type(candles)}, not a dict with 'candles' key")
            
    except Exception as e:
        print(f"Error in search_candles_from_db: {e}")

def check_database_structure(chronos):
    """Check the database structure to ensure it matches the examples."""
    print("\n=== Checking Database Structure ===")
    
    data_dir = chronos.project_root / "data"
    
    # Check symbols database
    symbols_db = data_dir / "symbols.db"
    if symbols_db.exists():
        print(f"\nSymbols database exists at: {symbols_db}")
        try:
            conn = sqlite3.connect(str(symbols_db))
            cursor = conn.cursor()
            
            # Check symbols table structure
            cursor.execute("PRAGMA table_info(symbols)")
            columns = cursor.fetchall()
            print("\nSymbols table columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
                
            # Expected columns in symbols table
            expected_columns = {
                'symbol_id', 'symbol', 'description', 'security_type', 
                'listing_exchange', 'is_tradable', 'is_quotable', 
                'currency', 'updated_at'
            }
            
            # Check for missing columns
            actual_columns = {col[1] for col in columns}
            missing_columns = expected_columns - actual_columns
            if not missing_columns:
                print("✓ Symbols table has all expected columns")
            else:
                print(f"✗ Missing expected columns: {missing_columns}")
                
            conn.close()
        except Exception as e:
            print(f"Error examining symbols database: {e}")
    else:
        print(f"Symbols database doesn't exist at: {symbols_db}")
    
    # Check market data database
    market_db = data_dir / "market_data.db"
    if market_db.exists():
        print(f"\nMarket data database exists at: {market_db}")
        try:
            conn = sqlite3.connect(str(market_db))
            cursor = conn.cursor()
            
            # Check candles table structure
            cursor.execute("PRAGMA table_info(candles)")
            columns = cursor.fetchall()
            print("\nCandles table columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
                
            # Expected columns in candles table
            expected_columns = {
                'symbol', 'start', 'end', 'low', 'high', 'open', 
                'close', 'volume', 'VWAP', 'interval'
            }
            
            # Check for missing columns
            actual_columns = {col[1] for col in columns}
            missing_columns = expected_columns - actual_columns
            if not missing_columns:
                print("✓ Candles table has all expected columns")
            else:
                print(f"✗ Missing expected columns: {missing_columns}")
                
            conn.close()
        except Exception as e:
            print(f"Error examining market data database: {e}")
    else:
        print(f"Market data database doesn't exist at: {market_db}")

def main():
    """Main function to run verification tests."""
    print("=== Chronos Implementation Verification ===")
    print(f"Current directory: {os.getcwd()}")
    print(f"Running verification at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests in sequence
    chronos, api = verify_chronos_attributes()
    symbol, symbol_info = test_get_symbol_info(chronos)
    test_get_candles(chronos, symbol)
    test_get_updated_candles(chronos, symbol)
    test_search_candles_from_db(chronos, symbol)
    check_database_structure(chronos)
    
    print("\n=== Verification Completed ===")
    print("Run test_chronos.py for more detailed tests and debugging.")

if __name__ == "__main__":
    main() 