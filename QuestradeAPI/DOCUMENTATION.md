# Questrade API Wrapper Documentation

This document provides detailed technical documentation for the `QuestradeAPI` class, including all available methods, parameters, return types, and usage examples.

## Table of Contents

- [Authentication](#authentication)
- [Account Methods](#account-methods)
- [Market Data Methods](#market-data-methods)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Enumerations](#enumerations)
- [Troubleshooting](#troubleshooting)
- [Type References](#type-references)

## Authentication

### Constructor

```python
QuestradeAPI(refresh_token: Optional[str] = None, token_path: Optional[str] = None, 
             max_retries: int = 3, enforce_rate_limit: bool = True)
```

Initialize the Questrade API wrapper with optional refresh token or token file path.

**Parameters:**
- `refresh_token` (Optional[str]): Refresh token for Questrade authentication. If not provided, will attempt to read from token file or prompt user.
- `token_path` (Optional[str]): Path to the token JSON file. If not provided, defaults to `[project_root]/secrets/questrade_token.json`.
- `max_retries` (int): Maximum number of retries when hitting rate limits. Default is 3.
- `enforce_rate_limit` (bool): Whether to enforce rate limits and wait if needed. Default is True.

**Example:**
```python
# Method 1: Direct token
api = QuestradeAPI(refresh_token="your_refresh_token")

# Method 2: Default token file
api = QuestradeAPI()

# Method 3: Custom token file path
api = QuestradeAPI(token_path="/path/to/token.json")

# Method 4: With rate limiting options
api = QuestradeAPI(max_retries=5, enforce_rate_limit=True)
```

### authenticate

```python
authenticate() -> bool
```

Authenticate with the Questrade API using the refresh token.

**Returns:**
- `bool`: True if authentication was successful, False otherwise.

**Example:**
```python
success = api.authenticate()
if success:
    print("Authentication successful")
else:
    print("Authentication failed")
```

## Account Methods

### get_accounts

```python
get_accounts() -> Dict[str, List[Dict[str, Any]]]
```

Get all accounts associated with the user.

**Returns:**
- Dictionary containing:
  - `accounts` (List[Dict]): List of account records with:
    - `type` (str): Account type (e.g., 'Margin', 'TFSA', 'RRSP')
    - `number` (str): Account number
    - `status` (str): Account status (e.g., 'Active')
    - `isPrimary` (bool): Whether this is the primary account
    - `isBilling` (bool): Whether this is the billing account
    - `clientAccountType` (str): Client account type

**Example:**
```python
accounts = api.get_accounts()
account_id = accounts['accounts'][0]['number']  # Get first account number
```

### get_account_positions

```python
get_account_positions(account_id: str) -> Dict[str, List[Dict[str, Any]]]
```

Get positions for a specific account.

**Parameters:**
- `account_id` (str): Account number to retrieve positions for

**Returns:**
- Dictionary containing:
  - `positions` (List[Dict]): List of position records with:
    - `symbol` (str): Position symbol
    - `symbolId` (int): Internal symbol identifier 
    - `openQuantity` (float): Position quantity remaining open
    - `closedQuantity` (float): Portion of position closed today
    - `currentMarketValue` (float): Market value of position
    - `currentPrice` (float): Current price of position symbol
    - `averageEntryPrice` (float): Average price paid for position
    - `closedPnL` (float): Realized profit/loss
    - `openPnL` (float): Unrealized profit/loss
    - `totalCost` (float): Total cost of the position
    - `isRealTime` (bool): If real-time quote used for PnL
    - `isUnderReorg` (bool): If symbol undergoing reorganization

**Example:**
```python
positions = api.get_account_positions("12345678")
for position in positions['positions']:
    print(f"{position['symbol']}: {position['openQuantity']} shares")
```

### get_account_balances

```python
get_account_balances(account_id: str) -> Dict[str, Dict[str, Any]]
```

Get balances for a specific account.

**Parameters:**
- `account_id` (str): Account number to retrieve balances for

**Returns:**
- Dictionary containing:
  - `perCurrencyBalances` (List[Dict]): List of balances per currency:
    - `currency` (str): Currency code
    - `cash` (float): Cash balance
    - `marketValue` (float): Market value
    - `totalEquity` (float): Total equity
    - `buyingPower` (float): Buying power
    - `maintenanceExcess` (float): Maintenance excess
    - `isRealTime` (bool): Whether values are real-time
  - `combinedBalances` (List[Dict]): List of combined balances
  - `sodPerCurrencyBalances` (List[Dict]): Start-of-day balances per currency
  - `sodCombinedBalances` (List[Dict]): Start-of-day combined balances

**Example:**
```python
balances = api.get_account_balances("12345678")
cad_balance = next((b for b in balances['perCurrencyBalances'] if b['currency'] == 'CAD'), None)
if cad_balance:
    print(f"CAD Cash: ${cad_balance['cash']}, Buying Power: ${cad_balance['buyingPower']}")
```

### get_account_executions

```python
get_account_executions(account_id: str, start_time: Optional[str] = None, 
                     end_time: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]
```

Get executions for a specific account.

**Parameters:**
- `account_id` (str): Account number to retrieve executions for
- `start_time` (Optional[str]): Start time for filtering executions (ISO format with timezone)
- `end_time` (Optional[str]): End time for filtering executions (ISO format with timezone)

**Returns:**
- Dictionary containing:
  - `executions` (List[Dict]): List of execution records with:
    - `symbol` (str): Symbol that was traded
    - `symbolId` (int): Internal symbol identifier
    - `quantity` (float): Quantity that was executed
    - `side` (str): Side of the execution (e.g., 'Buy', 'Sell')
    - `price` (float): Price at which the execution occurred
    - `id` (int): Execution identifier
    - `orderId` (int): Order identifier
    - and more execution details...

**Example:**
```python
executions = api.get_account_executions(
    "12345678",
    start_time="2023-01-01T00:00:00.000000-05:00",
    end_time="2023-01-31T23:59:59.000000-05:00"
)
```

### get_account_orders

```python
get_account_orders(account_id: str, start_time: Optional[str] = None, 
                 end_time: Optional[str] = None, state: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]
```

Get orders for a specific account.

**Parameters:**
- `account_id` (str): Account number to retrieve orders for
- `start_time` (Optional[str]): Start time for filtering orders (ISO format with timezone)
- `end_time` (Optional[str]): End time for filtering orders (ISO format with timezone)
- `state` (Optional[str]): State of orders to retrieve (All, Open, Closed)

**Returns:**
- Dictionary containing:
  - `orders` (List[Dict]): List of order records with order details

**Example:**
```python
orders = api.get_account_orders(
    "12345678",
    start_time="2023-01-01T00:00:00.000000-05:00",
    end_time="2023-01-31T23:59:59.000000-05:00",
    state="All"
)
```

### get_account_activities

```python
get_account_activities(account_id: str, start_time: Optional[str] = None, 
                     end_time: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]
```

Get account activities for a specific account.

**Parameters:**
- `account_id` (str): Account number to retrieve activities for
- `start_time` (Optional[str]): Start time for filtering activities (ISO format with timezone)
- `end_time` (Optional[str]): End time for filtering activities (ISO format with timezone)

**Returns:**
- Dictionary containing:
  - `activities` (List[Dict]): List of activity records including:
    - `tradeDate` (str): Date of the activity
    - `transactionDate` (str): Transaction date of the activity
    - `settlementDate` (str): Settlement date of the activity
    - `action` (str): Type of action (e.g., 'Buy', 'Sell', 'Dividend')
    - `symbol` (str): Symbol involved in the activity
    - `description` (str): Description of the activity
    - and more activity details...

**Example:**
```python
activities = api.get_account_activities(
    "12345678",
    start_time="2023-01-01T00:00:00.000000-05:00",
    end_time="2023-01-31T23:59:59.000000-05:00"
)
```

## Market Data Methods

### get_symbols

```python
get_symbols(symbols: List[str] = None, symbol_names: List[str] = None) -> Dict[str, List[Dict[str, Any]]]
```

Get symbol data for a list of symbols.

**Parameters:**
- `symbols` (List[str], optional): List of symbol IDs to retrieve
- `symbol_names` (List[str], optional): List of symbol names to retrieve

**Returns:**
- Dictionary containing:
  - `symbols` (List[Dict]): List of symbol records with detailed information

**Example:**
```python
# Using symbol IDs
symbol_data = api.get_symbols(symbols=["9001", "9002"])

# Using symbol names
symbol_data = api.get_symbols(symbol_names=["AAPL", "MSFT", "GOOG"])
```

### get_symbol

```python
get_symbol(symbol_id: str) -> Dict[str, List[Dict[str, Any]]]
```

Get detailed information about a specific symbol.

**Parameters:**
- `symbol_id` (str): Symbol ID to retrieve

**Returns:**
- Dictionary containing:
  - `symbols` (List[Dict]): List with a single symbol record containing detailed information

**Example:**
```python
symbol_info = api.get_symbol("9001")
apple_details = symbol_info['symbols'][0]
print(f"Market cap: ${apple_details.get('marketCap')}")
```

### search_symbols

```python
search_symbols(prefix: str, offset: int = 0) -> Dict[str, List[Dict[str, Any]]]
```

Search for symbols by prefix.

**Parameters:**
- `prefix` (str): The prefix to search for
- `offset` (int, optional): The offset for pagination. Default is 0.

**Returns:**
- Dictionary containing:
  - `symbols` (List[Dict]): List of symbol records matching the search

**Example:**
```python
results = api.search_symbols("APP")  # Will find AAPL, etc.
for symbol in results['symbols']:
    print(f"{symbol['symbol']} - {symbol['description']}")
```

### get_symbol_options

```python
get_symbol_options(symbol_id: str) -> Dict
```

Get option chain for a symbol.

**Parameters:**
- `symbol_id` (str): Symbol ID to retrieve option chain for

**Returns:**
- Dictionary containing:
  - `options` (List[Dict]): List of option chain elements per expiry date

**Example:**
```python
options = api.get_symbol_options("9001")  # AAPL symbol ID
for expiry in options['options']:
    print(f"Expiry date: {expiry['expiryDate']}")
    for root in expiry['chainPerRoot']:
        for strike in root['chainPerStrikePrice']:
            print(f"  Strike: ${strike['strikePrice']}")
```

### get_markets

```python
get_markets() -> Dict[str, List[Dict[str, Any]]]
```

Get information about supported markets.

**Returns:**
- Dictionary containing:
  - `markets` (List[Dict]): List of market records with details on trading hours and venues

**Example:**
```python
markets = api.get_markets()
for market in markets['markets']:
    print(f"{market['name']}: {market['tradingVenues']}")
    print(f"  Hours: {market['startTime']} - {market['endTime']}")
```

### get_quotes

```python
get_quotes(symbol_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]
```

Get quotes for a list of symbols.

**Parameters:**
- `symbol_ids` (List[str]): List of internal symbol identifiers

**Returns:**
- Dictionary containing:
  - `quotes` (List[Dict]): List of quote records with current market data

**Example:**
```python
quotes = api.get_quotes(["9001", "9002"])  # AAPL and another symbol
for quote in quotes['quotes']:
    print(f"{quote['symbol']}: ${quote['lastTradePrice']} (vol: {quote['volume']})")
```

### get_quote

```python
get_quote(symbol_id: str) -> Dict[str, List[Dict[str, Any]]]
```

Get quote for a single symbol.

**Parameters:**
- `symbol_id` (str): Internal symbol identifier

**Returns:**
- Dictionary containing:
  - `quotes` (List[Dict]): List with a single quote record with current market data

**Example:**
```python
quote = api.get_quote("9001")  # AAPL symbol ID
aapl_quote = quote['quotes'][0]
print(f"Bid: ${aapl_quote['bidPrice']} x {aapl_quote['bidSize']}")
print(f"Ask: ${aapl_quote['askPrice']} x {aapl_quote['askSize']}")
```

### get_candles

```python
get_candles(symbol_id: str, start_time: str, end_time: str, 
           interval: str = 'OneDay') -> Dict[str, Any]
```

Get historical candles for a symbol.

**Parameters:**
- `symbol_id` (str): Symbol ID
- `start_time` (str): Start time in ISO format with timezone
- `end_time` (str): End time in ISO format with timezone
- `interval` (str, optional): Candle interval. Default is 'OneDay'.
  - Valid intervals: OneMinute, TwoMinutes, ThreeMinutes, FourMinutes, FiveMinutes, 
    TenMinutes, FifteenMinutes, TwentyMinutes, HalfHour, OneHour, TwoHours, FourHours, 
    OneDay, OneWeek, OneMonth, OneYear

**Returns:**
- Dictionary containing:
  - `candles` (List[Dict]): List of candle records with OHLC and volume data

**Example:**
```python
candles = api.get_candles(
    symbol_id="9001",  # AAPL symbol ID
    start_time="2023-01-01T00:00:00.000000-05:00",
    end_time="2023-01-31T23:59:59.000000-05:00",
    interval="OneDay"
)
for candle in candles['candles']:
    print(f"{candle['start']}: Open ${candle['open']}, Close ${candle['close']}")
```

### get_option_quotes

```python
get_option_quotes(option_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]
```

Get quotes for a list of option symbols.

**Parameters:**
- `option_ids` (List[str]): List of option symbol identifiers

**Returns:**
- Dictionary containing:
  - `quotes` (List[Dict]): List of option quote records with current market data and greeks

**Example:**
```python
# First get option IDs from symbol options
options_data = api.get_symbol_options("9001")  # AAPL
option_ids = []
for expiry in options_data['options'][:1]:  # Just first expiry
    for root in expiry['chainPerRoot'][:1]:
        for strike in root['chainPerStrikePrice'][:2]:  # First two strikes
            if 'callSymbolId' in strike:
                option_ids.append(strike['callSymbolId'])

# Now get quotes for these options
if option_ids:
    option_quotes = api.get_option_quotes(option_ids)
    for quote in option_quotes['quotes']:
        print(f"{quote['symbol']}: ${quote['lastTradePrice']} (IV: {quote['volatility']}%)")
```

### get_strategy_quotes

```python
get_strategy_quotes(variant_id: str) -> Dict[str, List[Dict[str, Any]]]
```

Get quotes for a strategy (multi-leg orders).

**Parameters:**
- `variant_id` (str): Strategy variant identifier

**Returns:**
- Dictionary containing:
  - `quotes` (List[Dict]): List of strategy quote records

**Example:**
```python
# This requires a variant ID which is typically obtained through other API calls
strategy_quotes = api.get_strategy_quotes("your_variant_id")
```

### get_time

```python
get_time() -> Dict[str, str]
```

Get current server time.

**Returns:**
- Dictionary containing:
  - `time` (str): Current server time in ISO format

**Example:**
```python
server_time = api.get_time()
print(f"Server time: {server_time['time']}")
```

## Error Handling

The Questrade API wrapper provides structured error handling through exception classes that match the Questrade API error format.

### Error Classes

- `QuestradeAPIError`: Base exception class for all Questrade API errors
- `QuestradeGeneralError`: Raised for general API errors that don't result in order creation
- `QuestradeOrderError`: Raised for order processing errors that result in order creation
- `QuestradeRateLimitError`: Raised when rate limits are hit and maximum retries are exhausted

### Error Properties

Each error class includes:
- `code`: The error code returned by the API
- `message`: The error message returned by the API
- `status_code`: The HTTP status code of the failed request

Additionally, `QuestradeOrderError` includes:
- `order_id`: The ID of the created order
- `orders`: A list of order records

`QuestradeRateLimitError` includes:
- `retry_after`: Seconds to wait before retrying

### Example Usage

```python
from QuestradeAPI.CustomWrapper import (
    QuestradeAPI, 
    QuestradeAPIError, 
    QuestradeGeneralError, 
    QuestradeOrderError,
    QuestradeRateLimitError
)

try:
    api = QuestradeAPI()
    # Attempt an API operation
    data = api.get_account_positions("12345678")
except QuestradeRateLimitError as e:
    print(f"Rate limit error: {e.code} - {e.message}")
    print(f"Retry after: {e.retry_after} seconds")
except QuestradeOrderError as e:
    print(f"Order error: {e.code} - {e.message}")
    print(f"Order ID: {e.order_id}")
    print(f"Orders: {e.orders}")
except QuestradeGeneralError as e:
    print(f"General error: {e.code} - {e.message}")
    print(f"HTTP status: {e.status_code}")
except QuestradeAPIError as e:
    print(f"API error: {e.code} - {e.message}")
```

### Common Error Codes

| Code | Description | Possible Solution |
|------|-------------|-------------------|
| 1000 | Authentication failed | Check refresh token and reauthorize |
| 1001 | Invalid endpoint | Verify API endpoint path is correct |
| 1002 | Invalid or malformed argument | Check parameter types and formats |
| 1006 | Rate limit exceeded | Implement backoff strategy or reduce request rate |
| 1011 | Connection error | Check network connection |
| 1017 | Access token is invalid | Reauthenticate to get a new token |
| 1021 | Unexpected error | Check API status and retry |

## Rate Limiting

The wrapper includes built-in support for rate limiting to prevent hitting Questrade API rate limits.

### Rate Limits

Questrade API has the following rate limits:
- Account endpoints: 30 requests/second, 30,000 requests/hour
- Market data endpoints: 20 requests/second, 15,000 requests/hour

### Rate Limiting Features

- **Automatic tracking**: Monitors request rates for both per-second and per-hour limits
- **Adaptive waiting**: Automatically waits when approaching rate limits
- **Header parsing**: Parses Questrade's rate limit headers (`X-RateLimit-Remaining`, `X-RateLimit-Reset`)
- **Configurable retries**: Customizable maximum retry attempts when rate limits are reached
- **Disable option**: Can disable rate limiting for specialized use cases

### Rate Limit Parameters

When initializing the API, you can configure rate limiting behavior:

```python
# Enable rate limiting with 5 retry attempts
api = QuestradeAPI(enforce_rate_limit=True, max_retries=5)

# Disable rate limiting (not recommended for production)
api = QuestradeAPI(enforce_rate_limit=False)
```

### Rate Limit Error

When rate limits are hit and maximum retries are exhausted, a `QuestradeRateLimitError` is raised with:

- `code`: Error code (1006 for rate limiting)
- `message`: Error message
- `status_code`: HTTP status (429)
- `retry_after`: Seconds to wait before retrying

### Handling Rate Limits

For best practices with rate limiting:

1. **Keep rate limiting enabled** for production applications
2. **Set appropriate retry counts** based on your application's needs
3. **Implement exponential backoff** for failed requests
4. **Monitor rate limit headers** in responses to adapt request rates

Example with custom handling:

```python
from QuestradeAPI.CustomWrapper import QuestradeAPI, QuestradeRateLimitError
import time

api = QuestradeAPI(enforce_rate_limit=True, max_retries=3)

def get_data_with_backoff(max_attempts=5):
    attempt = 0
    while attempt < max_attempts:
        try:
            return api.get_time()
        except QuestradeRateLimitError as e:
            attempt += 1
            wait_time = e.retry_after * (2 ** attempt)  # Exponential backoff
            print(f"Rate limited. Waiting {wait_time} seconds before retry {attempt}")
            time.sleep(wait_time)
            
    raise Exception("Maximum retry attempts reached")
```

## Enumerations

The wrapper provides Python enumerations for the various enum types used in the Questrade API. These can be imported from `QuestradeAPI.enums`.

### Using Enumerations

Enumerations provide type safety and auto-completion in supported IDEs:

```python
from QuestradeAPI.enums import OrderType, OrderTimeInForce, HistoricalDataGranularity

# Use enums for type safety and code completion
candles = api.get_candles(
    symbol_id="9001",
    start_time="2023-01-01T00:00:00-05:00",
    end_time="2023-01-31T23:59:59-05:00",
    interval=HistoricalDataGranularity.OneDay
)
```

### Available Enumerations

#### Currency
```python
class Currency(str, Enum):
    """Supported currency codes."""
    USD = "USD"  # US dollar
    CAD = "CAD"  # Canadian dollar
```

#### ListingExchange
```python
class ListingExchange(str, Enum):
    """Supported listing exchanges."""
    TSX = "TSX"               # Toronto Stock Exchange
    TSXV = "TSXV"             # Toronto Venture Exchange
    CNSX = "CNSX"             # Canadian National Stock Exchange
    MX = "MX"                 # Montreal Exchange
    NASDAQ = "NASDAQ"         # NASDAQ
    NYSE = "NYSE"             # New York Stock Exchange
    NYSEAM = "NYSEAM"         # NYSE AMERICAN
    ARCA = "ARCA"             # NYSE Arca
    OPRA = "OPRA"             # Option Reporting Authority
    PinkSheets = "PinkSheets" # Pink Sheets
    OTCBB = "OTCBB"           # OTC Bulletin Board
```

#### AccountType
```python
class AccountType(str, Enum):
    """Supported user account types."""
    Cash = "Cash"       # Cash account
    Margin = "Margin"   # Margin account
    TFSA = "TFSA"       # Tax Free Savings Account
    RRSP = "RRSP"       # Registered Retirement Savings Plan
    FHSA = "FHSA"       # First Home Savings Account
    SRRSP = "SRRSP"     # Spousal RRSP
    LRRSP = "LRRSP"     # Locked-In RRSP
    LIRA = "LIRA"       # Locked-In Retirement Account
    LIF = "LIF"         # Life Income Fund
    RIF = "RIF"         # Retirement Income Fund
    SRIF = "SRIF"       # Spousal RIF
    LRIF = "LRIF"       # Locked-In RIF
    RRIF = "RRIF"       # Registered RIF
    PRIF = "PRIF"       # Prescribed RIF
    RESP = "RESP"       # Individual Registered Education Savings Plan
    FRESP = "FRESP"     # Family RESP
```

Additional enumerations include:
- `ClientAccountType`
- `AccountStatus`
- `TickType`
- `OptionType`
- `OptionDurationType`
- `OptionExerciseType`
- `SecurityType`
- `OrderStateFilterType`
- `OrderAction`
- `OrderSide`
- `OrderType`
- `OrderTimeInForce`
- `OrderState`
- `HistoricalDataGranularity`
- `OrderClass`
- `StrategyType`

## Troubleshooting

### Common Issues and Solutions

#### Authentication Failures

**Issue**: `Authentication failed` or `Access token is invalid` errors

**Solutions**:
- Verify your refresh token is valid and not expired
- Check if token_path is correct and accessible
- Try obtaining a new refresh token from Questrade App Hub
- Ensure your system clock is correctly synchronized

#### Rate Limiting Issues

**Issue**: Frequent `Rate limit exceeded` errors despite rate limiting being enabled

**Solutions**:
- Increase the `max_retries` parameter
- Implement additional backoff in your application
- Distribute requests more evenly over time
- Consider caching frequently accessed data

#### Date Format Issues

**Issue**: Date/time related errors in API calls

**Solutions**:
- Ensure all date/time strings include timezone information
- Use the format `YYYY-MM-DDThh:mm:ss.000000-05:00` for Eastern Time
- For consistency, consider using Python's datetime with proper formatting:
  ```python
  import datetime
  now = datetime.datetime.now()
  formatted_time = now.strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
  ```

#### Connection Issues

**Issue**: `Connection error` or timeouts

**Solutions**:
- Check your network connection
- Verify that firewalls are not blocking the connection
- Implement retry logic for transient network issues
- Check Questrade system status for outages

## Type References

The following Python type annotations are used throughout the API:

- `Dict[str, Any]`: Dictionary with string keys and any value type
- `List[Dict[str, Any]]`: List of dictionaries
- `Optional[str]`: String that may be None
- `bool`: Boolean value (True/False)
- `int`: Integer value
- `float`: Floating point value 