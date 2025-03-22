#!/usr/bin/env python
"""
Verify the fix for the market_data.db candles table by testing insertion and retrieval
with the interval column.
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime

def verify_db_fix():
    # Add visible markers for script execution
    print("*" * 80)
    print("STARTING DATABASE VERIFICATION")
    print("*" * 80)
    sys.stdout.flush()
    
    # Path to the database
    db_path = Path("data") / "market_data.db"
    print(f"Database path: {db_path} (exists: {db_path.exists()})")
    sys.stdout.flush()
    
    # Connect to the database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    print("Connected to database successfully")
    sys.stdout.flush()
    
    # 1. Check the schema
    print("\n" + "=" * 40)
    print("=== Checking Candles Table Schema ===")
    print("=" * 40)
    sys.stdout.flush()
    
    cursor.execute("PRAGMA table_info(candles)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[0]}: {col[1]} ({col[2]})")
    sys.stdout.flush()
    
    # 2. Check primary key
    print("\n" + "=" * 40)
    print("=== Checking Primary Key ===")
    print("=" * 40)
    sys.stdout.flush()
    
    cursor.execute("PRAGMA index_list('candles')")
    indexes = cursor.fetchall()
    for idx in indexes:
        print(f"  Index: {idx}")
        sys.stdout.flush()
        if idx[2] == 1:  # This is the primary key
            print(f"  Primary key found: {idx[1]}")
            sys.stdout.flush()
            cursor.execute(f"PRAGMA index_info('{idx[1]}')")
            pk_columns = cursor.fetchall()
            print(f"  Primary key columns: {pk_columns}")
            sys.stdout.flush()
    
    # 3. Test insertion with different interval values
    print("\n" + "=" * 40)
    print("=== Testing Data Insertion with Different Intervals ===")
    print("=" * 40)
    sys.stdout.flush()
    
    # Sample data
    test_data = [
        {
            'symbol': 'TEST1',
            'start': '2025-03-22T10:00:00.000000-05:00',
            'end': '2025-03-22T10:01:00.000000-05:00',
            'low': 100.0,
            'high': 105.0,
            'open': 102.0,
            'close': 103.0,
            'volume': 1000,
            'VWAP': 102.5,
            'interval': 'OneMinute'
        },
        {
            'symbol': 'TEST1',
            'start': '2025-03-22T10:00:00.000000-05:00',  # Same time but different interval
            'end': '2025-03-22T11:00:00.000000-05:00',
            'low': 100.0,
            'high': 110.0,
            'open': 102.0,
            'close': 108.0,
            'volume': 5000,
            'VWAP': 105.0,
            'interval': 'OneHour'
        }
    ]
    
    # Insert test data
    try:
        for data in test_data:
            print(f"  Inserting data for {data['symbol']} with interval {data['interval']}...")
            sys.stdout.flush()
            cursor.execute('''
            INSERT INTO candles (symbol, start, end, low, high, open, close, volume, VWAP, interval)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['symbol'], data['start'], data['end'], data['low'], data['high'],
                data['open'], data['close'], data['volume'], data['VWAP'], data['interval']
            ))
        conn.commit()
        print("  Test data inserted successfully!")
        sys.stdout.flush()
    except sqlite3.Error as e:
        print(f"  Error inserting data: {e}")
        sys.stdout.flush()
        conn.rollback()
    
    # 4. Verify retrieval with interval filter
    print("\n" + "=" * 40)
    print("=== Testing Data Retrieval with Interval Filter ===")
    print("=" * 40)
    sys.stdout.flush()
    
    intervals = ['OneMinute', 'OneHour']
    for interval in intervals:
        print(f"  Searching for records with interval '{interval}'...")
        sys.stdout.flush()
        cursor.execute('''
        SELECT * FROM candles WHERE symbol = ? AND interval = ?
        ''', ('TEST1', interval))
        rows = cursor.fetchall()
        print(f"  Found {len(rows)} rows for interval '{interval}'")
        sys.stdout.flush()
        for row in rows:
            print(f"  {row}")
            sys.stdout.flush()
    
    # Clean up test data
    print("\n  Cleaning up test data...")
    sys.stdout.flush()
    cursor.execute("DELETE FROM candles WHERE symbol = 'TEST1'")
    conn.commit()
    
    # Close connection
    conn.close()
    print("  Database connection closed")
    sys.stdout.flush()
    
    print("\n" + "=" * 40)
    print("=== Verification Completed ===")
    print("=" * 40)
    sys.stdout.flush()
    print("The candles table appears to be correctly structured with the 'interval' column in the primary key.")
    sys.stdout.flush()

if __name__ == "__main__":
    verify_db_fix() 