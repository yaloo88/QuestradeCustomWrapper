# Questrade Custom API Wrapper

A comprehensive Python wrapper for the Questrade API, providing easy access to account information and market data.

## Features

- **Simple Authentication**: Handles OAuth2 authentication flow with automatic token refresh
- **Comprehensive API Coverage**: Access to all major Questrade API endpoints
- **Rate Limiting**: Built-in rate limit handling to prevent API throttling
- **Error Handling**: Structured exception handling with detailed error information
- **Type Annotations**: Full Python type hints for better IDE integration
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

### Method 1: Clone and Install as Package (Recommended)

This method makes the API callable from any Python script on your system:

```bash
# Clone the repository
git clone https://github.com/yaloo88/QuestradeCustomAPIWrapper.git
cd QuestradeCustomAPIWrapper

# Install as a package in development mode
pip install -e .
```

After installation, you can import the package from any Python script:

```python
# From any script on your system
from QuestradeAPI import QuestradeAPI

api = QuestradeAPI()
```

### Method 2: Clone and Install Dependencies Only

```bash
# Clone the repository
git clone https://github.com/yaloo88/QuestradeCustomAPIWrapper.git
cd QuestradeCustomAPIWrapper

# Install dependencies
pip install -r requirements.txt
```

When using this method, you'll need to import directly from the project:

```python
# Need to import from specific path
from QuestradeAPI.CustomWrapper import QuestradeAPI
```

## Quick Start

```python
from questrade_custom_api import QuestradeAPI

# Initialize with a refresh token
api = QuestradeAPI(refresh_token="your_refresh_token")

# Or use a saved token file (default location or custom)
api = QuestradeAPI()  # Uses default token path
api = QuestradeAPI(token_path="/path/to/token.json")

# Get account information
accounts = api.get_accounts()
account_id = accounts['accounts'][0]['number']

# Get positions for an account
positions = api.get_account_positions(account_id)
for position in positions['positions']:
    print(f"{position['symbol']}: {position['openQuantity']} shares at ${position['currentPrice']}")

# Get market data
symbol_info = api.search_symbols("AAPL")
symbol_id = symbol_info['symbols'][0]['symbolId']

# Get historical data
import datetime
from datetime import timedelta

end_time = datetime.datetime.now()
start_time = end_time - timedelta(days=30)

# Format dates in ISO 8601 format with timezone
start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")

candles = api.get_candles(
    symbol_id=symbol_id,
    start_time=start_time_str,
    end_time=end_time_str,
    interval="OneDay"
)
```

## Documentation

For detailed API documentation, see the [DOCUMENTATION.md](QuestradeAPI/DOCUMENTATION.md) file.

## Error Handling

The wrapper provides structured error handling through exception classes:

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
    data = api.get_account_positions("12345678")
except QuestradeRateLimitError as e:
    print(f"Rate limit error: {e.code} - {e.message}")
    print(f"Retry after: {e.retry_after} seconds")
except QuestradeOrderError as e:
    print(f"Order error: {e.code} - {e.message}")
    print(f"Order ID: {e.order_id}")
except QuestradeGeneralError as e:
    print(f"General error: {e.code} - {e.message}")
except QuestradeAPIError as e:
    print(f"API error: {e.code} - {e.message}")
```

## Rate Limiting

The wrapper includes built-in rate limiting to prevent hitting Questrade API limits:

```python
# Enable rate limiting with custom retry attempts
api = QuestradeAPI(enforce_rate_limit=True, max_retries=5)

# Disable rate limiting (not recommended for production)
api = QuestradeAPI(enforce_rate_limit=False)
```

## Examples

Check the [notebooks/Examples.ipynb](notebooks/Examples.ipynb) for more usage examples.

## Trading Functionality

The wrapper supports placing and managing orders:

```python
# Place a market order
order_response = api.place_order(
    account_id="12345678",
    symbol_id="9001",  # AAPL symbol ID
    quantity=10,
    order_type="Market",
    action="Buy",
    time_in_force="Day"
)

# Place a limit order
order_response = api.place_order(
    account_id="12345678",
    symbol_id="9001",  # AAPL symbol ID
    quantity=10,
    order_type="Limit",
    limit_price=150.00,
    action="Buy",
    time_in_force="Day"
)

# Get order status
order_id = order_response['orders'][0]['id']
order_status = api.get_order(account_id="12345678", order_id=order_id)

# Cancel an order
cancel_response = api.cancel_order(account_id="12345678", order_id=order_id)
```

## Automated Git Tools

This repository includes scripts to help with Git operations:

- `commit.sh` - Bash script for Unix/Linux/macOS
- `Commit.ps1` - PowerShell script for Windows

These scripts provide an interactive way to stage, commit, and push changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgements

- [Questrade API Documentation](https://www.questrade.com/api/documentation/getting-started)
- Thanks to all contributors who have helped improve this wrapper 

## Using the API from Any Script

There are several ways to use the Questrade Custom API Wrapper from any script after cloning the repository:

### 1. Install as a Package (Recommended)

The easiest and recommended approach is to install the wrapper as a Python package:

```bash
# After cloning
cd QuestradeCustomAPIWrapper
pip install -e .
```

Then in any script:

```python
from questrade_custom_api import QuestradeAPI

api = QuestradeAPI()
# Use the API...
```

### 2. Add to Python Path

If you prefer not to install the package, you can add the repository to your Python path:

```python
import sys
import os
from pathlib import Path

# Add the repository root to Python path
repo_path = Path('/path/to/QuestradeCustomAPIWrapper')  # Change this to your actual path
sys.path.append(str(repo_path))

# Now import the API
from QuestradeAPI.CustomWrapper import QuestradeAPI

api = QuestradeAPI()
# Use the API...
```

### 3. Set Environment Variable

You could also set the PYTHONPATH environment variable:

```bash
# In bash/sh
export PYTHONPATH=$PYTHONPATH:/path/to/QuestradeCustomAPIWrapper

# In PowerShell
$env:PYTHONPATH += ";C:\path\to\QuestradeCustomAPIWrapper"
```

Then in your script:

```python
from QuestradeAPI.CustomWrapper import QuestradeAPI

api = QuestradeAPI()
# Use the API...
```

### 4. Use the Examples

Check out the examples in the `/examples` directory for sample scripts that show how to use the API. 
