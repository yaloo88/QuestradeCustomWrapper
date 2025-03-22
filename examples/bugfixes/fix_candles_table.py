#!/usr/bin/env python
"""
Fix the candles table in market_data.db to add the 'interval' column 
and update the primary key to include it.
"""

import sqlite3
import os
from pathlib import Path

def fix_candles_table():
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Path to the database
    db_path = data_dir / "market_data.db"
    
    # Connect to the database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if the candles table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='candles'")
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        # Create a backup of the existing data
        print("Creating a backup of existing data...")
        cursor.execute("CREATE TABLE IF NOT EXISTS candles_backup AS SELECT * FROM candles")
        
        # Drop the existing table
        print("Dropping existing candles table...")
        cursor.execute("DROP TABLE candles")
    
    # Create the table with the correct schema
    print("Creating new candles table with the correct schema...")
    cursor.execute('''
    CREATE TABLE candles (
        symbol TEXT,
        start TEXT,
        end TEXT,
        low REAL,
        high REAL,
        open REAL,
        close REAL,
        volume INTEGER,
        VWAP REAL,
        interval TEXT DEFAULT 'OneMinute',
        PRIMARY KEY (symbol, start, interval)
    )
    ''')
    
    # Restore data from backup if it existed
    if table_exists:
        print("Restoring data from backup...")
        cursor.execute('''
        INSERT INTO candles (symbol, start, end, low, high, open, close, volume, VWAP)
        SELECT symbol, start, end, low, high, open, close, volume, VWAP FROM candles_backup
        ''')
        
        # Drop the backup table
        print("Dropping backup table...")
        cursor.execute("DROP TABLE candles_backup")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Candles table has been successfully fixed!")

if __name__ == "__main__":
    fix_candles_table() 