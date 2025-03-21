# Questrade API Wrapper Quick Start Guide

This quick start guide will help you set up and start using the Questrade API wrapper in just a few minutes.

## Prerequisites

- Python 3.6 or higher
- A Questrade account
- A Questrade API refresh token

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/QuestradeCustomAPIWrapper.git
cd QuestradeCustomAPIWrapper
```

## Step 2: Get Your Questrade API Token

1. Log in to your Questrade account at https://login.questrade.com
2. Navigate to App Hub > Register a personal app
3. Note down your refresh token

## Step 3: Basic Setup

Create a Python script or Jupyter notebook with the following code:

```python
from QuestradeAPI.CustomWrapper import QuestradeAPI

# Initialize the API with your refresh token
api = QuestradeAPI(refresh_token="YOUR_REFRESH_TOKEN")

# Or, to have the token saved automatically for future use:
# api = QuestradeAPI()  # Will prompt for token if not found
```

## Step 4: Retrieve Your Accounts

```python
# Get all accounts
accounts = api.get_accounts()
print(accounts)

# Get the first account ID for future use
account_id = accounts['accounts'][0]['number']
```

## Step 5: Get Account Details

```python
# Get account balances
balances = api.get_account_balances(account_id)
print(f"Cash balance (CAD): {balances['perCurrencyBalances'][0]['cash']}")

# Get account positions
positions = api.get_account_positions(account_id)
for position in positions['positions']:
    print(f"Symbol: {position['symbol']}, Quantity: {position['openQuantity']}, Market Value: {position['currentMarketValue']}")
```

## Step 6: Access Market Data

```python
# Search for a symbol
apple = api.search_symbols("AAPL")
symbol_id = apple['symbols'][0]['symbolId']

# Get current quotes
quotes = api.get_quotes([symbol_id])
print(f"Current price: {quotes['quotes'][0]['lastTradePrice']}")

# Get historical data
import datetime
from datetime import timedelta

# Get data for the last 30 days
end_time = datetime.datetime.now().isoformat()
start_time = (datetime.datetime.now() - timedelta(days=30)).isoformat()

candles = api.get_candles(
    symbol_id=symbol_id,
    start_time=start_time,
    end_time=end_time,
    interval="OneDay"
)

# Print the closing prices
for candle in candles['candles']:
    print(f"Date: {candle['end']}, Close: {candle['close']}")
```

## Common Tasks

### Authentication Refresh

The API wrapper automatically handles token refresh. When you make API requests, if the token has expired, it will automatically attempt to refresh it.

```python
# Force a re-authentication
api.authenticate()
```

### Error Handling

The wrapper provides custom exception classes that provide detailed information about API errors:

```python
from QuestradeAPI.CustomWrapper import (
    QuestradeAPI, 
    QuestradeAPIError, 
    QuestradeGeneralError,
    QuestradeOrderError,
    QuestradeRateLimitError
)

try:
    data = api.get_account_positions(account_id)
except QuestradeRateLimitError as e:
    print(f"Rate limit error: {e.code} - {e.message}")
    print(f"Retry after: {e.retry_after} seconds")
except QuestradeGeneralError as e:
    print(f"General error: {e.code} - {e.message}")
    print(f"HTTP status: {e.status_code}")
except QuestradeAPIError as e:
    print(f"API error: {e.code} - {e.message}")
```

### Rate Limiting

The API wrapper includes built-in rate limiting to prevent exceeding Questrade's API limits:

```python
# Enable rate limiting with 5 retry attempts
api = QuestradeAPI(enforce_rate_limit=True, max_retries=5)

# For high-throughput applications, implement custom backoff
from time import sleep

def get_data_with_backoff(api, symbol_id, max_attempts=5):
    attempt = 0
    while attempt < max_attempts:
        try:
            return api.get_quote(symbol_id)
        except QuestradeRateLimitError as e:
            attempt += 1
            wait_time = e.retry_after * (2 ** attempt)  # Exponential backoff
            print(f"Rate limited. Waiting {wait_time} seconds before retry {attempt}")
            sleep(wait_time)
            
    raise Exception("Maximum retry attempts reached")
```

## Next Steps

For more detailed information on all available methods, parameters, error handling, rate limiting, and enumerations, see the complete [documentation](./QuestradeAPI/DOCUMENTATION.md).

You can also check out the example scripts in the `scripts` directory for detailed usage examples:

- `api_examples.py`: Basic API usage examples
- `error_handling_example.py`: Error handling examples
- `rate_limit_example.py`: Rate limiting examples

Happy trading! 