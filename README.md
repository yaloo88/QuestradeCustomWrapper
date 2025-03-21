# Questrade Custom API Wrapper

A Python wrapper for the Questrade API that simplifies authentication and provides easy-to-use methods for accessing market data, account information, and performing trading operations with the Questrade platform.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Authentication](#authentication)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Enumerations](#enumerations)
- [Examples](#examples)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project provides a convenient Python wrapper around the Questrade REST API. It handles authentication, token refresh, and provides intuitive methods for querying account information, market data, and executing trades.

Features:
- OAuth2 authentication with automatic token refresh
- Methods for accessing account information (balances, positions, orders, executions)
- Market data access (quotes, candles, symbols, options)
- Built-in rate limiting to prevent API limit errors
- Structured error handling with informative exceptions
- Type-safe enumerations for various API parameters
- Well-documented API with type hints
- Example scripts for common use cases

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/QuestradeCustomAPIWrapper.git
cd QuestradeCustomAPIWrapper
```

The wrapper requires Python 3.6+ and the following dependencies:
- requests
- pathlib
- typing

## Authentication

To use the Questrade API, you need a refresh token from Questrade. You can obtain one by:

1. Log in to your Questrade account at https://login.questrade.com
2. Go to App Hub > Register a personal app
3. Get your refresh token

The wrapper can be initialized in several ways:

```python
# Method 1: Provide the refresh token directly
api = QuestradeAPI(refresh_token="your_refresh_token")

# Method 2: Store the token in a file (default: secrets/questrade_token.json)
# The wrapper will read from this file automatically
api = QuestradeAPI()

# Method 3: Specify a custom path for the token file
api = QuestradeAPI(token_path="/path/to/your/token.json")
```

If no refresh token is available, the wrapper will prompt you to enter one.

## Usage

Here's a quick example of how to use the wrapper:

```python
from QuestradeAPI.CustomWrapper import QuestradeAPI

# Initialize the API
questrade = QuestradeAPI()

# Get all accounts
accounts = questrade.get_accounts()

# Get balances for the first account
account_id = accounts['accounts'][0]['number']
balances = questrade.get_account_balances(account_id)

# Get market data
candles = questrade.get_candles(
    symbol_id="9001", 
    start_time="2023-01-01T00:00:00-05:00",
    end_time="2023-01-31T00:00:00-05:00", 
    interval="OneDay"
)
```

## API Reference

For a complete list of available methods and parameters, see the [API Documentation](./QuestradeAPI/DOCUMENTATION.md).

### Account Methods

- `get_accounts()`: Get all accounts associated with the user
- `get_account_positions(account_id)`: Get positions for a specific account
- `get_account_balances(account_id)`: Get balances for a specific account
- `get_account_executions(account_id, start_time, end_time)`: Get executions for a specific account
- `get_account_orders(account_id, start_time, end_time, state)`: Get orders for a specific account
- `get_account_activities(account_id, start_time, end_time)`: Get account activities

### Market Data Methods

- `get_symbols(symbols)`: Get symbol data for a list of symbols
- `get_symbol(symbol_id)`: Get detailed information for a specific symbol
- `search_symbols(prefix, offset)`: Search for symbols by prefix
- `get_symbol_options(symbol_id)`: Get options for a symbol
- `get_markets()`: Get information about supported markets
- `get_quotes(symbol_ids)`: Get quotes for a list of symbols
- `get_quote(symbol_id)`: Get quote for a single symbol
- `get_candles(symbol_id, start_time, end_time, interval)`: Get historical candles for a symbol
- `get_option_quotes(option_ids)`: Get quotes for option symbols
- `get_strategy_quotes(variant_id)`: Get quotes for strategy variants
- `get_time()`: Get current server time

## Error Handling

The wrapper provides structured error handling through exception classes that match the Questrade API error format:

### Error Classes

- `QuestradeAPIError`: Base exception class for all Questrade API errors
- `QuestradeGeneralError`: Raised for general API errors that don't result in order creation
- `QuestradeOrderError`: Raised for order processing errors that result in order creation
- `QuestradeRateLimitError`: Raised when rate limits are exceeded and maximum retries are exhausted

### Error Properties

Each error class includes:
- `code`: The error code returned by the API
- `message`: The error message returned by the API
- `status_code`: The HTTP status code of the failed request

Additionally, `QuestradeOrderError` includes:
- `order_id`: The ID of the created order
- `orders`: A list of order records

### Example Usage

```python
from QuestradeAPI.CustomWrapper import QuestradeAPI, QuestradeGeneralError, QuestradeOrderError, QuestradeRateLimitError

try:
    api = QuestradeAPI()
    # Attempt to access an invalid endpoint
    result = api._make_request('v1/invalid/endpoint')
except QuestradeRateLimitError as e:
    print(f"Rate limit exceeded: {e.code} - {e.message}")
    print(f"Try again after: {e.retry_after} seconds")
except QuestradeGeneralError as e:
    print(f"General error: {e.code} - {e.message}")
    print(f"HTTP status: {e.status_code}")
except QuestradeOrderError as e:
    print(f"Order error: {e.code} - {e.message}")
    print(f"Order ID: {e.order_id}")
    print(f"Orders: {e.orders}")
```

The wrapper automatically handles authentication errors and will attempt to re-authenticate if needed.

## Rate Limiting

The wrapper includes built-in support for rate limiting to prevent hitting Questrade API rate limits. It handles:

- Account endpoints: 30 requests/second, 30,000 requests/hour
- Market data endpoints: 20 requests/second, 15,000 requests/hour

### Rate Limiting Features

- **Automatic tracking**: Monitors request rates for both per-second and per-hour limits
- **Adaptive waiting**: Automatically waits when approaching rate limits
- **Header parsing**: Parses Questrade's rate limit headers (`X-RateLimit-Remaining`, `X-RateLimit-Reset`)
- **Configurable retries**: Customizable maximum retry attempts when rate limits are reached
- **Disable option**: Can disable rate limiting for specialized use cases

### Rate Limit Error

When rate limits are hit and maximum retries are exhausted, a `QuestradeRateLimitError` is raised with:

- `code`: Error code (1006 for rate limiting)
- `message`: Error message
- `status_code`: HTTP status (429)
- `retry_after`: Seconds to wait before retrying

### Example Usage

```python
from QuestradeAPI.CustomWrapper import QuestradeAPI, QuestradeRateLimitError

# Enable rate limiting with 3 retry attempts (default)
api = QuestradeAPI(enforce_rate_limit=True, max_retries=3)

try:
    # Make rapid API requests
    for i in range(50):
        result = api.get_time()
except QuestradeRateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    print(f"Try again after: {e.retry_after} seconds")
```

To disable rate limiting (not recommended for production):

```python
# Disable rate limiting
api = QuestradeAPI(enforce_rate_limit=False)
```

## Enumerations

The wrapper provides Python enumerations for the various enum types used in the Questrade API. Import them from `QuestradeAPI.enums`:

```python
from QuestradeAPI.enums import Currency, AccountType, OrderType, HistoricalDataGranularity

# Use enums for safer, more readable code
candles = api.get_candles(
    symbol_id="9001",
    start_time="2023-01-01T00:00:00-05:00",
    end_time="2023-01-31T23:59:59-05:00",
    interval=HistoricalDataGranularity.OneDay
)
```

Available enumerations include:
- `Currency`: Currency codes (USD, CAD)
- `AccountType`: Account types (Cash, Margin, TFSA, etc.)
- `OrderType`: Order types (Market, Limit, etc.)
- `OrderSide`: Order sides (Buy, Sell, Short, etc.)
- `HistoricalDataGranularity`: Candle intervals (OneMinute, OneDay, etc.)

For the complete list, see the [API Documentation](./QuestradeAPI/DOCUMENTATION.md#enumerations).

## Examples

The repository includes example scripts in the `scripts` directory that demonstrate common use cases:

- `api_examples.py`: Demonstrates basic API usage for accounts and market data
- `error_handling_example.py`: Shows how to properly handle various error conditions
- `rate_limit_example.py`: Demonstrates the rate limiting functionality

To run an example:

```bash
python -m scripts.api_examples
```

## Project Structure

```
QuestradeCustomAPIWrapper/
├── QuestradeAPI/
│   ├── CustomWrapper.py     # Main API wrapper class
│   ├── RateLimiter.py       # Rate limiting functionality
│   ├── enums.py             # Type-safe enumerations
│   └── DOCUMENTATION.md     # Detailed API documentation
├── scripts/
│   ├── api_examples.py      # Basic usage examples
│   ├── api_validator.py     # Validation test script
│   ├── error_handling_example.py  # Error handling demo
│   └── rate_limit_example.py      # Rate limiting demo
├── validation_results/      # Test results from validator
├── secrets/
│   └── questrade_token.json # Authentication token (not committed)
└── README.md                # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. #   Q u e s t r a d e C u s t o m W r a p p e r  
 