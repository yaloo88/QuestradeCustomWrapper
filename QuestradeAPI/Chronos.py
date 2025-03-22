from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

class Chronos:
    def __init__(self, api=None, project_root=None):
        self.api = api
        # Set project root
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Changed to get the package root directory instead of current working directory
            self.project_root = Path(__file__).parent.parent.resolve()
        
        # Database setup
        self.db_path = self.project_root / "data" / "symbols.db"
        self.db_path.parent.mkdir(exist_ok=True)  # Create data directory if it doesn't exist
        self.conn = None
        self.symbol_cache = {}  # Cache for frequently accessed symbols
        
        # Register adapter and converter for datetime
        sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
        sqlite3.register_converter("TIMESTAMP", lambda b: datetime.fromisoformat(b.decode()))
    
    def _ensure_db_connection(self):
        """Ensures database connection is established"""
        if self.conn is None:
            # Note the detect_types parameter
            self.conn = sqlite3.connect(str(self.db_path), detect_types=sqlite3.PARSE_DECLTYPES)
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")
            # Create the table if it doesn't exist
            cursor = self.conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS symbols (
                symbol_id INTEGER PRIMARY KEY,
                symbol TEXT UNIQUE,
                description TEXT,
                security_type TEXT,
                listing_exchange TEXT,
                is_tradable BOOLEAN,
                is_quotable BOOLEAN,
                currency TEXT,
                updated_at TIMESTAMP
            )
            ''')
            # Add index for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON symbols(symbol)')
            self.conn.commit()
        return self.conn
    
    def _db_to_api_format(self, db_data):
        """Convert database column format to API format"""
        return {
            'symbolId': db_data['symbol_id'],
            'symbol': db_data['symbol'],
            'description': db_data['description'],
            'securityType': db_data['security_type'],
            'listingExchange': db_data['listing_exchange'],
            'isTradable': db_data['is_tradable'],
            'isQuotable': db_data['is_quotable'],
            'currency': db_data['currency']
        }

    def _api_to_db_format(self, api_data):
        """Convert API format to database column format"""
        return (
            api_data['symbolId'],
            api_data['symbol'],
            api_data['description'],
            api_data['securityType'],
            api_data['listingExchange'],
            api_data['isTradable'],
            api_data['isQuotable'],
            api_data['currency'],
            datetime.now()
        )
    
    def get_symbol_info(self, symbol_name):
        """Get symbol information from cache, database or API, ensuring consistent return format."""
        # Check cache first
        if symbol_name in self.symbol_cache:
            print(f"Symbol {symbol_name} found in cache")
            return self.symbol_cache[symbol_name]
        
        # Ensure database connection
        self._ensure_db_connection()
        
        with self.conn:  # Auto-commits and handles rollbacks
            cursor = self.conn.cursor()
            
            # Try to get symbol from database first
            cursor.execute('SELECT * FROM symbols WHERE symbol = ?', (symbol_name,))
            columns = [desc[0] for desc in cursor.description]
            result = cursor.fetchone()
            
            if result:
                print(f"Symbol {symbol_name} found in database")
                # Convert DB column names to API format for consistency
                db_data = dict(zip(columns, result))
                symbol_data = self._db_to_api_format(db_data)
            else:
                print(f"Symbol {symbol_name} not found in database, fetching from API...")
                if not self.api:
                    raise ValueError("API instance is required to fetch symbol data")
                
                symbol_info = self.api.search_symbols(symbol_name)
                symbol_data = symbol_info['symbols'][0]
                
                # Save to database
                cursor.execute('''
                INSERT OR REPLACE INTO symbols 
                (symbol_id, symbol, description, security_type, listing_exchange, 
                 is_tradable, is_quotable, currency, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', self._api_to_db_format(symbol_data))
                print(f"Saved {symbol_data['symbol']} to database at {self.db_path}")
        
        # Cache the result before returning
        self.symbol_cache[symbol_name] = symbol_data
        return symbol_data

    def get_all_symbols(self):
        """
        Retrieves all symbols stored in the database.
        
        Returns:
            list: A list of dictionaries containing information for all symbols in the database.
        """
        self._ensure_db_connection()
        
        try:
            with self.conn:
                cursor = self.conn.cursor()
                
                # Fetch all symbols from the database
                cursor.execute('''
                SELECT symbol_id, symbol, description, security_type, listing_exchange, 
                       is_tradable, is_quotable, currency, updated_at
                FROM symbols
                ''')
                
                results = cursor.fetchall()
                
                if not results:
                    print("No symbols found in the database.")
                    return []
                
                # Column names for the results
                columns = ['symbol_id', 'symbol', 'description', 'security_type', 'listing_exchange', 
                           'is_tradable', 'is_quotable', 'currency', 'updated_at']
                
                # Convert the results to a list of dictionaries
                symbols_list = []
                for result in results:
                    db_data = dict(zip(columns, result))
                    symbol_data = self._db_to_api_format(db_data)
                    symbols_list.append(symbol_data)
                
                print(f"Retrieved {len(symbols_list)} symbols from the database.")
                return symbols_list
        
        except sqlite3.OperationalError as e:
            print(f"Database error: {e}")
            print(f"Could not access database at: {self.db_path}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []
    
    def bulk_insert_symbols(self, symbol_data_list):
        """Insert multiple symbols at once for better performance"""
        self._ensure_db_connection()
        
        with self.conn:
            cursor = self.conn.cursor()
            cursor.executemany('''
            INSERT OR REPLACE INTO symbols 
            (symbol_id, symbol, description, security_type, listing_exchange, 
             is_tradable, is_quotable, currency, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [self._api_to_db_format(data) for data in symbol_data_list])
        
        # Update cache for each inserted symbol
        for data in symbol_data_list:
            self.symbol_cache[data['symbol']] = data
    
    def update_stale_symbols(self, days_threshold=90):
        """Update symbols that haven't been refreshed in the specified number of days"""
        if not self.api:
            raise ValueError("API instance is required to update stale symbols")
        
        self._ensure_db_connection()
        
        # Calculate the cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT symbol FROM symbols WHERE updated_at < ?', 
                          (cutoff_date,))
            stale_symbols = [row[0] for row in cursor.fetchall()]
        
        # Update each stale symbol by fetching fresh data from API
        for symbol in stale_symbols:
            print(f"Updating stale data for {symbol}")
            # Force API fetch by temporarily removing from database
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('DELETE FROM symbols WHERE symbol = ?', (symbol,))
            
            # This will get from API and save to DB
            self.get_symbol_info(symbol)
    
    def search_symbols_in_db(self, search_term):
        """Search for symbols containing the search term"""
        self._ensure_db_connection()
        
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT * FROM symbols 
            WHERE symbol LIKE ? OR description LIKE ?
            ''', (f'%{search_term}%', f'%{search_term}%'))
            
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            
            return [self._db_to_api_format(dict(zip(columns, row))) for row in results]
    
    def get_db_stats(self):
        """Get statistics about the database"""
        self._ensure_db_connection()
        
        with self.conn:
            cursor = self.conn.cursor()
            stats = {}
            
            # Count total symbols
            cursor.execute('SELECT COUNT(*) FROM symbols')
            stats['total_symbols'] = cursor.fetchone()[0]
            
            # Count by security type
            cursor.execute('SELECT security_type, COUNT(*) FROM symbols GROUP BY security_type')
            stats['by_security_type'] = dict(cursor.fetchall())
            
            # Count by exchange
            cursor.execute('SELECT listing_exchange, COUNT(*) FROM symbols GROUP BY listing_exchange')
            stats['by_exchange'] = dict(cursor.fetchall())
            
            # Get database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            stats['db_size_bytes'] = page_count * page_size
            
            return stats
    
    def optimize_db(self):
        """Run VACUUM to optimize the database"""
        self._ensure_db_connection()
        self.conn.execute("VACUUM")
        print("Database optimized")
    
    def clear_symbol_cache(self):
        """Clear the symbol cache"""
        self.symbol_cache = {}
    
    def get_candles(self, symbol, days=90, interval="OneMinute", force_refresh=False):
        """
        Get historical candle data for a symbol.
        
        Args:
            symbol (str): The stock symbol to get candles for
            days (int): Number of days of historical data to retrieve
            interval (str): Candle interval ("OneMinute", "OneDay", etc.)
            force_refresh (bool): Whether to force a refresh from the API even if data exists in the database
        
        Returns:
            pandas.DataFrame: DataFrame containing candle data
        """
        import pandas as pd
        import os
        
        # First get symbol info to get the symbol_id
        symbol_info = self.get_symbol_info(symbol_name=symbol)
        symbol_id = symbol_info['symbolId']
        
        # Get current time for end time
        end_time = datetime.now()
        
        # Create the data directory if it doesn't exist
        data_dir = self.project_root / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Set up market data db path
        market_db_path = data_dir / "market_data.db"
        
        # Connect to the database
        conn = sqlite3.connect(str(market_db_path))
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS candles (
            symbol TEXT,
            start TEXT,
            end TEXT,
            low REAL,
            high REAL,
            open REAL,
            close REAL,
            volume INTEGER,
            VWAP REAL,
            interval TEXT,
            PRIMARY KEY (symbol, start, interval)
        )
        ''')
        conn.commit()
        
        should_fetch_api = force_refresh
        start_time_str = None
        
        if not force_refresh:
            # Check if data exists in the database for this symbol and interval
            cursor.execute(
                "SELECT COUNT(*) FROM candles WHERE symbol = ? AND interval = ?", 
                (symbol, interval)
            )
            data_exists = cursor.fetchone()[0] > 0
            
            if data_exists:
                # Get the most recent candle timestamp
                cursor.execute("""
                    SELECT end FROM candles 
                    WHERE symbol = ? AND interval = ?
                    ORDER BY end DESC 
                    LIMIT 1
                """, (symbol, interval))
                last_end = cursor.fetchone()[0]
                
                # Check if we need to fetch new data
                # Convert the datetime from string ensuring both are timezone-aware
                try:
                    # Try to parse the datetime with timezone info
                    last_end_dt = datetime.fromisoformat(last_end.replace('Z', '+00:00'))
                    
                    # Make sure end_time is also timezone-aware if last_end_dt is
                    if last_end_dt.tzinfo is not None and end_time.tzinfo is None:
                        # Apply the same timezone as last_end_dt
                        end_time = end_time.replace(tzinfo=last_end_dt.tzinfo)
                    elif last_end_dt.tzinfo is None and end_time.tzinfo is not None:
                        # Apply the same timezone as end_time
                        last_end_dt = last_end_dt.replace(tzinfo=end_time.tzinfo)
                    
                    days_diff = (end_time - last_end_dt).days
                except (ValueError, TypeError) as e:
                    print(f"Error handling datetime: {e}")
                    # If there's an error, assume we need new data
                    days_diff = 1
                
                if days_diff > 0:
                    # We need to update with new data
                    start_time_str = last_end
                    should_fetch_api = True
                    print(f"Data exists for {symbol}. Fetching new data since {start_time_str}")
                else:
                    print(f"Using cached data for {symbol} with interval {interval}")
            else:
                # No data exists, need to fetch from API
                should_fetch_api = True
                # Calculate start time based on requested days
                start_time = end_time - timedelta(days=days)
                start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
                print(f"No data exists for {symbol} with interval {interval}. Fetching {days} days of data.")
        else:
            # Force refresh requested, calculate start time based on requested days
            start_time = end_time - timedelta(days=days)
            start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
            print(f"Force refreshing data for {symbol} with interval {interval}. Fetching {days} days of data.")
        
        if should_fetch_api:
            if not self.api:
                raise ValueError("API instance is required to fetch candle data")
                
            end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
            
            # Make API call for candles
            candles_response = self.api.get_candles(
                symbol_id=symbol_id,
                start_time=start_time_str,
                end_time=end_time_str,
                interval=interval
            )
            
            # Save the new candles to the database if there are any
            if 'candles' in candles_response and candles_response['candles']:
                # Convert to DataFrame for easier handling
                df = pd.DataFrame(candles_response['candles'])
                df['symbol'] = symbol
                df['interval'] = interval
                
                # Save to database
                for _, row in df.iterrows():
                    cursor.execute("""
                        INSERT OR REPLACE INTO candles 
                        (symbol, start, end, low, high, open, close, volume, VWAP, interval) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        symbol, 
                        row['start'], 
                        row['end'], 
                        row['low'], 
                        row['high'], 
                        row['open'], 
                        row['close'], 
                        row['volume'],
                        row.get('VWAP', None),  # Handle VWAP if present
                        interval
                    ))
                
                conn.commit()
                print(f"Saved {len(df)} new candles to database")
            else:
                print("No new candles found")
        
        # Retrieve all candles for the symbol and interval from the database
        cursor.execute("""
            SELECT symbol, start, end, low, high, open, close, volume, VWAP
            FROM candles
            WHERE symbol = ? AND interval = ?
            ORDER BY start
        """, (symbol, interval))
        
        columns = [description[0] for description in cursor.description]
        all_candles_data = cursor.fetchall()
        
        # Close database connection
        conn.close()
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(all_candles_data, columns=columns)
        
        # If DataFrame is not empty, convert date columns to datetime
        if not df.empty:
            for date_col in ['start', 'end']:
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], utc=True)
            
        print(f"Retrieved {len(df)} candles for {symbol}")
        return df
    
    def get_updated_candles(self, symbol, interval="OneMinute", as_dataframe=False):
        """
        Get updated candles for a symbol, fetching only new data if existing data is found.
        
        Args:
            symbol (str): The stock symbol to get candles for
            interval (str): Candle interval ("OneMinute", "OneDay", etc.)
            as_dataframe (bool): If True, returns results as pandas DataFrame instead of dict
        
        Returns:
            dict or pandas.DataFrame: Dictionary with 'candles' key containing list of candle dictionaries,
                                    or a pandas DataFrame if as_dataframe=True
        """
        import os
        import pandas as pd
        
        symbol_info = self.get_symbol_info(symbol_name=symbol)
        symbol_id = symbol_info['symbolId']
        
        # Get current time for end time
        end_time = datetime.now()
        
        # Create the data directory if it doesn't exist
        data_dir = self.project_root / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Set up market data db path
        market_db_path = data_dir / "market_data.db"
        
        # Connect to the database
        conn = sqlite3.connect(str(market_db_path))
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS candles (
            symbol TEXT,
            start TEXT,
            end TEXT,
            low REAL,
            high REAL,
            open REAL,
            close REAL,
            volume INTEGER,
            VWAP REAL,
            interval TEXT,
            PRIMARY KEY (symbol, start, interval)
        )
        ''')
        conn.commit()
        
        # Check if data exists in the database
        cursor.execute(
            "SELECT COUNT(*) FROM candles WHERE symbol = ? AND interval = ?", 
            (symbol, interval)
        )
        data_exists = cursor.fetchone()[0] > 0
        
        if data_exists:
            # True path - Read the last end value from the database
            cursor.execute("""
                SELECT end FROM candles 
                WHERE symbol = ? AND interval = ?
                ORDER BY end DESC 
                LIMIT 1
            """, (symbol, interval))
            last_end = cursor.fetchone()[0]
            start_time_str = last_end
            end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
            
            print(f"Data exists for {symbol}. Fetching new data since {start_time_str}")
        else:
            # False path - Assign default values
            # Default to getting 90 days of data if nothing exists
            start_time = end_time - timedelta(days=90)
            start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
            end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
            
            print(f"No data exists for {symbol}. Fetching 90 days of data.")
        
        # Make API call for new candles
        candles = self.api.get_candles(
            symbol_id=symbol_id,
            start_time=start_time_str,
            end_time=end_time_str,
            interval=interval
        )
        
        # Save the new candles to the database if there are any
        if 'candles' in candles and candles['candles']:
            # Convert to DataFrame for easier handling
            df = pd.DataFrame(candles['candles'])
            df['symbol'] = symbol
            df['interval'] = interval
            
            # Save to database
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT OR REPLACE INTO candles 
                    (symbol, start, end, low, high, open, close, volume, VWAP, interval) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, 
                    row['start'], 
                    row['end'], 
                    row['low'], 
                    row['high'], 
                    row['open'], 
                    row['close'], 
                    row['volume'],
                    row.get('VWAP', None),  # Handle VWAP if present
                    interval
                ))
            
            conn.commit()
            print(f"Saved {len(df)} new candles to database")
        else:
            print("No new candles found")
        
        # Retrieve all candles for the symbol from the database
        cursor.execute("""
            SELECT * FROM candles
            WHERE symbol = ? AND interval = ?
            ORDER BY start
        """, (symbol, interval))
        
        columns = [description[0] for description in cursor.description]
        all_candles_data = cursor.fetchall()
        
        # Convert to dictionary format similar to API response
        all_candles = []
        for row in all_candles_data:
            candle_dict = {columns[i]: row[i] for i in range(len(columns))}
            # Only remove interval as it's the same for all rows
            candle_dict.pop('interval', None)
            all_candles.append(candle_dict)
        
        conn.close()
        
        # Return as DataFrame if requested
        if as_dataframe:
            df = pd.DataFrame(all_candles)
            # Convert date columns to datetime if DataFrame is not empty
            if not df.empty:
                for date_col in ['start', 'end']:
                    if date_col in df.columns:
                        df[date_col] = pd.to_datetime(df[date_col], utc=True)
            return df
        
        # Otherwise return in original dict format
        return {"candles": all_candles}
    
    def search_candles_from_db(self, symbol, start_date=None, end_date=None, interval='OneMinute'):
        """
        Search for candles from the database without making API calls.
        
        Args:
            symbol (str): The stock symbol to search for
            start_date (str, optional): Start date in format 'YYYY-MM-DD'
            end_date (str, optional): End date in format 'YYYY-MM-DD'
            interval (str, optional): Candle interval (e.g., 'OneDay', 'OneMinute')
            
        Returns:
            dict: Dictionary with 'candles' key containing the matching candles
        """
        # Setup market data database path
        market_db_path = self.project_root / "data" / "market_data.db"
        
        # Check if database file exists
        if not market_db_path.exists():
            print(f"Database file not found at {market_db_path}")
            return {"candles": []}
        
        # Connect to the database
        conn = sqlite3.connect(str(market_db_path))
        cursor = conn.cursor()
        
        # Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='candles'")
        if not cursor.fetchone():
            print("Candles table does not exist in the database")
            conn.close()
            return {"candles": []}
        
        # Build the query based on provided parameters
        query = "SELECT * FROM candles WHERE symbol = ? AND interval = ?"
        params = [symbol, interval]
        
        if start_date:
            query += " AND start >= ?"
            params.append(f"{start_date}T00:00:00.000000-05:00")
        
        if end_date:
            query += " AND start <= ?"
            params.append(f"{end_date}T23:59:59.999999-05:00")
        
        query += " ORDER BY start"
        
        try:
            # Execute the query
            cursor.execute(query, params)
            
            columns = [description[0] for description in cursor.description]
            candles_data = cursor.fetchall()
            
            # Convert to dictionary format similar to API response
            candles = []
            for row in candles_data:
                candle_dict = {columns[i]: row[i] for i in range(len(columns))}
                # Only remove interval as it's the same for all rows
                candle_dict.pop('interval', None)
                candles.append(candle_dict)
            
            return {"candles": candles}
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return {"candles": []}
        finally:
            conn.close()
    
    def __del__(self):
        """Ensure database connection is closed when object is destroyed"""
        if hasattr(self, 'conn') and self.conn is not None:
            self.conn.close()