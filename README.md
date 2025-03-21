# Questrade Custom API Wrapper

![Python](https://img.shields.io/badge/Python-3.6%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow)

A Python wrapper for the Questrade API that simplifies authentication and provides easy-to-use methods for accessing market data, account information, and performing trading operations with the Questrade platform.

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/en/thumb/7/7e/Questrade_logo.svg/320px-Questrade_logo.svg.png" alt="Questrade Logo" width="200"/>
</p>

## 📋 Table of Contents

- [Overview](#-overview)
- [Installation](#-installation)
- [Authentication](#-authentication)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Error Handling](#-error-handling)
- [Rate Limiting](#-rate-limiting)
- [Enumerations](#-enumerations)
- [Examples](#-examples)
- [Project Structure](#-project-structure)
- [Development Tools](#-development-tools)
- [Contributing](#-contributing)
- [License](#-license)

## 🔍 Overview

This project provides a convenient Python wrapper around the Questrade REST API. It handles authentication, token refresh, and provides intuitive methods for querying account information, market data, and executing trades.

### Features:
- ✅ OAuth2 authentication with automatic token refresh
- ✅ Methods for accessing account information (balances, positions, orders, executions)
- ✅ Market data access (quotes, candles, symbols, options)
- ✅ Built-in rate limiting to prevent API limit errors
- ✅ Structured error handling with informative exceptions
- ✅ Type-safe enumerations for various API parameters
- ✅ Well-documented API with type hints
- ✅ Example scripts for common use cases

## 💾 Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/QuestradeCustomAPIWrapper.git
cd QuestradeCustomAPIWrapper
```

The wrapper requires Python 3.6+ and the following dependencies:
- requests
- pathlib
- typing

## 🔐 Authentication

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

## 🚀 Usage

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

## 📚 API Reference

For a complete list of available methods and parameters, see the [API Documentation](./QuestradeAPI/DOCUMENTATION.md).

### Account Methods

| Method | Description |
|--------|-------------|
| `get_accounts()` | Get all accounts associated with the user |
| `get_account_positions(account_id)` | Get positions for a specific account |
| `get_account_balances(account_id)` | Get balances for a specific account |
| `get_account_executions(account_id, start_time, end_time)` | Get executions for a specific account |
| `get_account_orders(account_id, start_time, end_time, state)` | Get orders for a specific account |
| `get_account_activities(account_id, start_time, end_time)` | Get account activities |

### Market Data Methods

| Method | Description |
|--------|-------------|
| `get_symbols(symbols)` | Get symbol data for a list of symbols |
| `get_symbol(symbol_id)` | Get detailed information for a specific symbol |
| `search_symbols(prefix, offset)` | Search for symbols by prefix |
| `get_symbol_options(symbol_id)` | Get options for a symbol |
| `get_markets()` | Get information about supported markets |
| `get_quotes(symbol_ids)` | Get quotes for a list of symbols |
| `