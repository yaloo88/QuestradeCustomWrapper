import os
import sys
from pathlib import Path
import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from .CustomWrapper import QuestradeAPI

class Chronos:
    def __init__(self, api=None):
        # Add project root to path
        self.project_root = Path('.').resolve()
        sys.path.append(str(self.project_root))
        print(f"Project root: {self.project_root}")
        
        # Initialize Questrade API if not provided
        self.api = api if api else QuestradeAPI()

    def get_symbol_info(self, symbol_name):
        """Get symbol information from database or API, ensuring consistent return format."""
        # Create or connect to a SQLite database
        db_path = self.project_root / "data" / "symbols.db"
        db_path.parent.mkdir(exist_ok=True)  # Create data directory if it doesn't exist
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create symbols table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS symbols (
            symbol_id INTEGER PRIMARY KEY,
            symbol TEXT,
            description TEXT,
            security_type TEXT,
            listing_exchange TEXT,
            is_tradable BOOLEAN,
            is_quotable BOOLEAN,
            currency TEXT,
            updated_at TIMESTAMP
        )
        ''')
        
        # Try to get symbol from database first
        cursor.execute('SELECT * FROM symbols WHERE symbol = ?', (symbol_name,))
        columns = [desc[0] for desc in cursor.description]
        result = cursor.fetchone()
        
        if result:
            print(f"Symbol {symbol_name} found in database")
            # Convert DB column names to API format for consistency
            db_data = dict(zip(columns, result))
            symbol_data = {
                'symbolId': db_data['symbol_id'],
                'symbol': db_data['symbol'],
                'description': db_data['description'],
                'securityType': db_data['security_type'],
                'listingExchange': db_data['listing_exchange'],
                'isTradable': db_data['is_tradable'],
                'isQuotable': db_data['is_quotable'],
                'currency': db_data['currency']
            }
        else:
            print(f"Symbol {symbol_name} not found in database, fetching from API...")
            symbol_info = self.api.search_symbols(symbol_name)
            symbol_data = symbol_info['symbols'][0]
            
            # Save to database
            cursor.execute('''
            INSERT OR REPLACE INTO symbols 
            (symbol_id, symbol, description, security_type, listing_exchange, 
             is_tradable, is_quotable, currency, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol_data['symbolId'],
                symbol_data['symbol'], 
                symbol_data['description'],
                symbol_data['securityType'],
                symbol_data['listingExchange'],
                symbol_data['isTradable'],
                symbol_data['isQuotable'],
                symbol_data['currency'],
                datetime.now()
            ))
            conn.commit()
            print(f"Saved {symbol_data['symbol']} to database at {db_path}")
        
        conn.close()
        return symbol_data

    def get_candles(self, symbol, days=90, interval="OneMinute", force_refresh=False):
        """
        Get historical candles for a given symbol.
        First tries to fetch from database, then falls back to API if needed.
        Updates existing data by fetching only new candles since the last recorded time.
        
        Parameters:
        - symbol: The stock symbol to fetch data for
        - days: Number of days of historical data to fetch
        - interval: Candle interval (e.g., "OneMinute", "OneDay")
        - force_refresh: If True, always fetch from API regardless of database
        """
        # Calculate date range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Format dates for API
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
        
        # Format dates for database query (simpler format)
        db_start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        db_end_time = end_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Database path
        db_path = self.project_root / "data" / "market_data.db"
        db_path.parent.mkdir(exist_ok=True)  # Create data directory if it doesn't exist
        
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS candles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            start_time TEXT,
            end_time TEXT,
            low REAL,
            high REAL,
            open REAL,
            close REAL,
            volume INTEGER,
            vwap REAL,
            updated_at TIMESTAMP
        )
        ''')
        
        # Check if we should fetch from database
        fetch_from_api = force_refresh
        candles_df = None
        api_start_time_str = start_time_str
        
        if not force_refresh:
            # Check if we have data for this symbol
            cursor.execute('''
            SELECT COUNT(*), MAX(end_time) FROM candles 
            WHERE symbol = ? AND start_time >= ? AND end_time <= ?
            ''', (symbol, db_start_time, db_end_time))
            
            result = cursor.fetchone()
            count = result[0]
            last_end_time = result[1]
            
            if count > 0 and last_end_time:
                print(f"Found {count} candles for {symbol} in database")
                
                # Get data from database
                query = '''
                SELECT * FROM candles 
                WHERE symbol = ? AND start_time >= ? AND end_time <= ?
                ORDER BY start_time
                '''
                candles_df = pd.read_sql_query(query, conn, params=(symbol, db_start_time, db_end_time))
                
                # Check if we need to update with newer data
                last_end_time_dt = datetime.fromisoformat(last_end_time.replace('Z', '+00:00'))
                
                # Convert to naive datetime by removing timezone info for comparison
                last_end_time_naive = last_end_time_dt.replace(tzinfo=None)
                
                # If the last candle is older than 1 day, fetch updates
                if (end_time - last_end_time_naive).total_seconds() > 86400:  # 86400 seconds = 1 day
                    print(f"Last candle is from {last_end_time}, fetching updates...")
                    fetch_from_api = True
                    
                    # Set API start time to the last candle's end time
                    # Add a small buffer (1 minute) to avoid duplicates
                    update_start_time = last_end_time_dt + timedelta(minutes=1)
                    api_start_time_str = update_start_time.strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
                    
                    print(f"Fetching new candles from {api_start_time_str} to {end_time_str}")
            else:
                print(f"No candles found for {symbol} in database")
                fetch_from_api = True
        
        # Fetch from API if needed
        if fetch_from_api:
            print(f"Fetching candles for {symbol} from API...")
            symbol_info = self.get_symbol_info(symbol)
            symbol_id = symbol_info['symbolId']
            
            candles_data = self.api.get_candles(
                symbol_id=symbol_id,
                start_time=api_start_time_str,
                end_time=end_time_str,
                interval=interval
            )
            
            # Extract candles from the response
            candles = candles_data.get('candles', [])
            
            if candles:
                print(f"Received {len(candles)} new candles from API")
                
                # Prepare data for batch insert
                candles_to_insert = []
                for candle in candles:
                    candles_to_insert.append((
                        symbol,
                        candle['start'],
                        candle['end'],
                        candle['low'],
                        candle['high'],
                        candle['open'],
                        candle['close'],
                        candle['volume'],
                        candle.get('VWAP', None),
                        datetime.now()
                    ))
                
                # Batch insert candles
                cursor.executemany('''
                INSERT OR REPLACE INTO candles 
                (symbol, start_time, end_time, low, high, open, close, volume, vwap, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', candles_to_insert)
                
                conn.commit()
                print(f"Saved {len(candles_to_insert)} candles for {symbol} to database")
                
                # If we already had data and just updated it, refresh our DataFrame
                if candles_df is not None:
                    query = '''
                    SELECT * FROM candles 
                    WHERE symbol = ? AND start_time >= ? AND end_time <= ?
                    ORDER BY start_time
                    '''
                    candles_df = pd.read_sql_query(query, conn, params=(symbol, db_start_time, db_end_time))
                else:
                    # Convert API response to DataFrame
                    candles_df = pd.DataFrame(candles)
            else:
                print(f"No new candles returned from API for {symbol}")
                if candles_df is None:
                    candles_df = pd.DataFrame()
        
        conn.close()
        return candles_df 