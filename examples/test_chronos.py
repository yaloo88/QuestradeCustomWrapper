#!/usr/bin/env python
"""
Confirmation script to verify Chronos functionality.
Run this script to test the various methods of the Chronos class.
"""

import os
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

def test_chronos_basics():
    """Test the basic functionality of the Chronos class"""
    print("\n=== Testing Chronos Basic Functionality ===")
    
    # Initialize API
    api = QuestradeAPI()
    print("API initialized")
    
    # Initialize Chronos
    chronos = Chronos(api=api)
    print(f"Chronos initialized with project root: {chronos.project_root}")
    print(f"Symbols database path: {chronos.db_path}")
    
    # Database setup check
    data_dir = chronos.project_root / "data"
    if data_dir.exists():
        print(f"Data directory exists at: {data_dir}")
        for db_file in data_dir.glob("*.db"):
            print(f"Database file found: {db_file.name}")
    else:
        print(f"Data directory does not exist at: {data_dir}")
    
    return chronos, api

def test_symbol_lookup(chronos):
    """Test symbol lookup functionality"""
    print("\n=== Testing Symbol Lookup ===")
    
    # Get a well-known symbol
    try:
        symbol = input("Enter a symbol to look up (default: AAPL): ").strip().upper() or "AAPL"
        symbol_info = chronos.get_symbol_info(symbol)
        print(f"Retrieved symbol info for {symbol}:")
        for key, value in symbol_info.items():
            print(f"  {key}: {value}")
        return symbol, symbol_info
    except Exception as e:
        print(f"Error looking up symbol: {e}")
        return None, None

def test_candles(chronos, symbol):
    """Test candle data retrieval and caching"""
    if not symbol:
        return
    
    print(f"\n=== Testing Candle Data for {symbol} ===")
    
    # Test get_candles method (returns pandas DataFrame)
    print("\n> Testing get_candles (pandas DataFrame return):")
    try:
        # First call might fetch from API
        print("First call (might fetch from API):")
        candles_df = chronos.get_candles(symbol=symbol, days=5, interval="OneDay")
        print(f"Retrieved {len(candles_df)} candles")
        if not candles_df.empty:
            print("Sample data:")
            print(candles_df.head())
        
        # Second call should use cache
        print("\nSecond call (should use cache):")
        candles_df2 = chronos.get_candles(symbol=symbol, days=5, interval="OneDay")
        print(f"Retrieved {len(candles_df2)} candles from cache")
        
        # Force refresh
        print("\nForced refresh (should fetch from API again):")
        candles_df3 = chronos.get_candles(symbol=symbol, days=5, interval="OneDay", force_refresh=True)
        print(f"Retrieved {len(candles_df3)} candles after forced refresh")
    except Exception as e:
        print(f"Error testing get_candles: {e}")
    
    # Test get_updated_candles method (returns API-like dictionary)
    print("\n> Testing get_updated_candles (dictionary return):")
    try:
        candles_dict = chronos.get_updated_candles(symbol=symbol, interval="OneDay")
        print(f"Retrieved {len(candles_dict['candles'])} candles")
        if candles_dict['candles']:
            print("Sample data (first candle):")
            first_candle = candles_dict['candles'][0]
            for key, value in first_candle.items():
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error testing get_updated_candles: {e}")
    
    # Test search_candles_from_db method
    print("\n> Testing search_candles_from_db:")
    try:
        # Get a date range for testing
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        
        candles_search = chronos.search_candles_from_db(
            symbol=symbol, 
            start_date=start_date,
            end_date=end_date,
            interval="OneDay"
        )
        
        print(f"Found {len(candles_search['candles'])} candles between {start_date} and {end_date}")
        if candles_search['candles']:
            print("Sample data (first candle):")
            first_candle = candles_search['candles'][0]
            for key, value in first_candle.items():
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error testing search_candles_from_db: {e}")

def test_db_operations(chronos):
    """Test database operations"""
    print("\n=== Testing Database Operations ===")
    
    # Get database stats
    try:
        stats = chronos.get_db_stats()
        print("\nDatabase Statistics:")
        print(f"  Total symbols: {stats['total_symbols']}")
        
        if 'by_security_type' in stats and stats['by_security_type']:
            print("  Security types:")
            for security_type, count in stats['by_security_type'].items():
                print(f"    {security_type}: {count}")
        
        if 'by_exchange' in stats and stats['by_exchange']:
            print("  Exchanges:")
            for exchange, count in stats['by_exchange'].items():
                print(f"    {exchange}: {count}")
    except Exception as e:
        print(f"Error getting database stats: {e}")
    
    # Test search functionality
    try:
        search_term = input("\nEnter a search term for symbols (default: tech): ").strip() or "tech"
        results = chronos.search_symbols_in_db(search_term)
        print(f"Found {len(results)} symbols matching '{search_term}'")
        for i, symbol in enumerate(results[:5]):  # Show first 5 results
            print(f"  {i+1}. {symbol['symbol']} - {symbol['description']} ({symbol['securityType']})")
        if len(results) > 5:
            print(f"  ... and {len(results)-5} more")
    except Exception as e:
        print(f"Error searching symbols: {e}")

def examine_db_files(chronos):
    """Examine database files directly"""
    print("\n=== Examining Database Files ===")
    
    data_dir = chronos.project_root / "data"
    if not data_dir.exists():
        print("Data directory doesn't exist")
        return
    
    # Check symbols database
    symbols_db = data_dir / "symbols.db"
    if symbols_db.exists():
        print(f"\nSymbols database exists ({symbols_db.stat().st_size} bytes)")
        try:
            conn = sqlite3.connect(str(symbols_db))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print("Tables in symbols database:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"  {table[0]}: {count} rows")
            conn.close()
        except Exception as e:
            print(f"Error examining symbols database: {e}")
    else:
        print("Symbols database doesn't exist")
    
    # Check market data database
    market_db = data_dir / "market_data.db"
    if market_db.exists():
        print(f"\nMarket data database exists ({market_db.stat().st_size} bytes)")
        try:
            conn = sqlite3.connect(str(market_db))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print("Tables in market data database:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"  {table[0]}: {count} rows")
                
                # If it's the candles table, show some stats
                if table[0] == 'candles':
                    cursor.execute("SELECT DISTINCT symbol, interval FROM candles")
                    symbols = cursor.fetchall()
                    print("  Symbols and intervals in candles table:")
                    for symbol_data in symbols:
                        cursor.execute(
                            "SELECT COUNT(*) FROM candles WHERE symbol = ? AND interval = ?", 
                            symbol_data
                        )
                        count = cursor.fetchone()[0]
                        print(f"    {symbol_data[0]} ({symbol_data[1]}): {count} candles")
            conn.close()
        except Exception as e:
            print(f"Error examining market data database: {e}")
    else:
        print("Market data database doesn't exist")

def main():
    """Main function to run all tests"""
    print("=== Chronos Confirmation Script ===")
    print(f"Current directory: {os.getcwd()}")
    print(f"Running tests at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests in sequence
    chronos, api = test_chronos_basics()
    symbol, symbol_info = test_symbol_lookup(chronos)
    test_candles(chronos, symbol)
    test_db_operations(chronos)
    examine_db_files(chronos)
    
    print("\n=== Tests Completed ===")

if __name__ == "__main__":
    main() 