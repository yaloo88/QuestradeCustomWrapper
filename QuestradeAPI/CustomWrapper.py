import os
import json
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

# Import our rate limiter
from .RateLimiter import RateLimiter, ApiCategory


class QuestradeAPIError(Exception):
    """Base exception class for Questrade API errors."""
    
    def __init__(self, code: str, message: str, status_code: int = None):
        """
        Initialize a new Questrade API Error.
        
        Args:
            code (str): The error code returned by the API
            message (str): The error message returned by the API
            status_code (int, optional): The HTTP status code
        """
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(f"Questrade API Error {code}: {message}")


class QuestradeGeneralError(QuestradeAPIError):
    """Exception for general errors that do not result in an order being created."""
    pass


class QuestradeOrderError(QuestradeAPIError):
    """Exception for order processing errors that result in an order being created."""
    
    def __init__(self, code: str, message: str, order_id: int, orders: List[Dict[str, Any]], status_code: int = None):
        """
        Initialize a new Questrade Order Error.
        
        Args:
            code (str): The error code returned by the API
            message (str): The error message returned by the API
            order_id (int): The ID of the created order
            orders (List[Dict]): List of order records
            status_code (int, optional): The HTTP status code
        """
        self.order_id = order_id
        self.orders = orders
        super().__init__(code, message, status_code)
        # Override the error message to include order information
        self.__str__ = lambda: f"Questrade Order Error {code}: {message} (Order ID: {order_id})"


class QuestradeRateLimitError(QuestradeGeneralError):
    """Exception for rate limit errors."""
    
    def __init__(self, code: str, message: str, status_code: int, retry_after: float = None):
        """
        Initialize a new Questrade Rate Limit Error.
        
        Args:
            code (str): The error code returned by the API
            message (str): The error message returned by the API
            status_code (int): The HTTP status code
            retry_after (float, optional): The time to wait before retrying in seconds
        """
        self.retry_after = retry_after
        super().__init__(code, message, status_code)
        # Override the error message to include retry information
        if retry_after:
            self.__str__ = lambda: f"Questrade Rate Limit Error {code}: {message} (Retry after: {retry_after}s)"


class QuestradeAPI:
    """
    A custom wrapper for the Questrade API that handles authentication and provides
    methods for common API operations.
    """
    
    def __init__(self, refresh_token: Optional[str] = None, token_path: Optional[str] = None, 
                 max_retries: int = 3, enforce_rate_limit: bool = True):
        """
        Initialize the Questrade API wrapper.
        
        Args:
            refresh_token: Optional refresh token to use for authentication
            token_path: Optional custom path to the token file
            max_retries: Maximum number of retries when hitting rate limits
            enforce_rate_limit: Whether to enforce rate limits and wait if needed
        """
        self.refresh_token = refresh_token
        
        # Set default token path if not provided
        if token_path is None:
            # Get the project root directory
            project_root = Path(__file__).parent.parent.resolve()
            self.token_path = os.path.join(project_root, 'secrets', 'questrade_token.json')
        else:
            self.token_path = token_path
            
        # Initialize API connection properties
        self.api_server = None
        self.access_token = None
        self.token_type = None
        self.expires_in = None
        
        # Initialize rate limiting
        self.rate_limiter = RateLimiter()
        self.max_retries = max_retries
        self.enforce_rate_limit = enforce_rate_limit
        
        # Authenticate on initialization
        self.authenticate()
    
    def authenticate(self) -> bool:
        """
        Authenticate with the Questrade API using the refresh token.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        # If no refresh token provided, try to read from file
        if self.refresh_token is None:
            if os.path.exists(self.token_path):
                try:
                    with open(self.token_path, 'r') as f:
                        token_data = json.load(f)
                    self.refresh_token = token_data['refresh_token']
                except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
                    print(f"Error reading token file: {e}")
                    return False
            else:
                # Prompt user for refresh token if file doesn't exist
                self.refresh_token = input("Please enter your Questrade refresh token: ")
                if not self.refresh_token:
                    print("No refresh token provided")
                    return False
        
        # Get new token
        url = f"https://login.questrade.com/oauth2/token?grant_type=refresh_token&refresh_token={self.refresh_token}"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Authentication failed: {response.text}")
            return False
            
        response_json = response.json()
        
        # Update instance properties
        self.api_server = response_json['api_server']
        self.access_token = response_json['access_token']
        self.token_type = response_json['token_type']
        self.expires_in = response_json['expires_in']
        self.refresh_token = response_json['refresh_token']
        
        # Save response to json file
        try:
            os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
            with open(self.token_path, 'w') as f:
                json.dump(response_json, f, indent=4)
        except PermissionError:
            print("Permission denied when trying to save token file. Try running with admin privileges or saving to a different location.")
        
        return True
    
    def _parse_rate_limit_headers(self, response, category):
        """
        Parse rate limit headers from the response and update the rate limiter.
        
        Args:
            response: Response object from requests
            category: ApiCategory for this request
        """
        # Check for rate limit headers
        remaining = response.headers.get('X-RateLimit-Remaining')
        reset = response.headers.get('X-RateLimit-Reset')
        
        if remaining is not None and reset is not None:
            try:
                remaining_int = int(remaining)
                reset_float = float(reset)
                self.rate_limiter.update_limits(category, remaining_int, reset_float)
            except (ValueError, TypeError):
                # If we can't parse the headers, just ignore them
                pass
    
    def _make_request(self, endpoint: str, method: str = 'GET', params: Optional[Dict] = None, 
                     data: Optional[Dict] = None, retry_count: int = 0) -> Dict:
        """
        Make a request to the Questrade API.
        
        Args:
            endpoint: API endpoint to call
            method: HTTP method (GET, POST, etc.)
            params: Optional query parameters
            data: Optional data for POST requests
            retry_count: Current retry attempt (used internally for recursion)
            
        Returns:
            Dict: JSON response from the API
            
        Raises:
            QuestradeGeneralError: For general API errors
            QuestradeOrderError: For order processing errors
            QuestradeRateLimitError: For rate limit errors
            requests.exceptions.RequestException: For network-related errors
        """
        # Ensure we have a valid token
        if not self.access_token or not self.api_server:
            if not self.authenticate():
                raise QuestradeGeneralError("1000", "Authentication failed", None)
        
        # Get the API category for rate limiting
        category = self.rate_limiter.get_category_for_endpoint(endpoint)
        
        # Check if we need to wait for rate limiting
        if self.enforce_rate_limit:
            wait_time = self.rate_limiter.wait_if_needed(category)
            if wait_time > 0:
                if retry_count < self.max_retries:
                    # Sleep and retry
                    time.sleep(wait_time)
                    return self._make_request(endpoint, method, params, data, retry_count + 1)
                else:
                    # We've reached the maximum number of retries
                    raise QuestradeRateLimitError(
                        "1006", "Rate limit exceeded. Maximum retry attempts reached.", 
                        429, wait_time
                    )
        
        # Construct the full URL
        url = f"{self.api_server}{endpoint.lstrip('/')}"
        
        # Set up headers
        headers = {
            'Authorization': f'{self.token_type} {self.access_token}'
        }
        
        # Make the request
        try:
            # Record this request for rate limiting
            self.rate_limiter.record_request(category)
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                headers['Content-Type'] = 'application/json'
                response = requests.post(url, headers=headers, params=params, json=data)
            elif method.upper() == 'PUT':
                headers['Content-Type'] = 'application/json'
                response = requests.put(url, headers=headers, params=params, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Parse rate limit headers to update our rate limiter
            self._parse_rate_limit_headers(response, category)
            
            # Handle rate limit exceeded
            if response.status_code == 429:
                retry_after = response.headers.get('X-RateLimit-Reset')
                retry_seconds = None
                if retry_after:
                    try:
                        retry_seconds = float(retry_after) - time.time()
                        retry_seconds = max(0, retry_seconds)
                    except (ValueError, TypeError):
                        retry_seconds = 1.0  # Default to 1 second if we can't parse
                
                if retry_count < self.max_retries and retry_seconds is not None:
                    # Sleep and retry
                    time.sleep(retry_seconds)
                    return self._make_request(endpoint, method, params, data, retry_count + 1)
                else:
                    # We've reached the maximum number of retries
                    raise QuestradeRateLimitError(
                        "1006", "Rate limit exceeded. Maximum retry attempts reached.", 
                        429, retry_seconds
                    )
            
            # Check for successful response
            if response.status_code >= 400:
                # Handle API errors
                try:
                    error_data = response.json()
                    error_code = str(error_data.get('code', '0'))
                    error_message = error_data.get('message', 'Unknown error')
                    
                    # Check if this is an order error (has orderId and orders)
                    if 'orderId' in error_data and 'orders' in error_data:
                        order_id = error_data.get('orderId')
                        orders = error_data.get('orders', [])
                        raise QuestradeOrderError(error_code, error_message, order_id, orders, response.status_code)
                    else:
                        raise QuestradeGeneralError(error_code, error_message, response.status_code)
                except json.JSONDecodeError:
                    # If we can't parse the response as JSON, raise a general error with the response text
                    if response.status_code == 404:
                        # Common 404 error is "Invalid endpoint"
                        raise QuestradeGeneralError("1001", "Invalid endpoint", response.status_code)
                    else:
                        raise QuestradeGeneralError("1021", f"Unexpected error: {response.text}", response.status_code)
            
            # If we get here, the request was successful
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            # If we get a 401, try to re-authenticate once
            response = e.response
            if response.status_code == 401:
                if self.authenticate():
                    # Retry the request with the new token
                    return self._make_request(endpoint, method, params, data, retry_count)
                else:
                    # Authentication failed
                    raise QuestradeGeneralError("1017", "Access token is invalid", 401)
            
            # For other HTTP errors, try to parse the API error response
            try:
                error_data = response.json()
                error_code = str(error_data.get('code', '0'))
                error_message = error_data.get('message', str(e))
                
                # Check if this is an order error (has orderId and orders)
                if 'orderId' in error_data and 'orders' in error_data:
                    order_id = error_data.get('orderId')
                    orders = error_data.get('orders', [])
                    raise QuestradeOrderError(error_code, error_message, order_id, orders, response.status_code)
                else:
                    raise QuestradeGeneralError(error_code, error_message, response.status_code)
            except (ValueError, KeyError, json.JSONDecodeError):
                # If we can't parse the response as JSON, raise a general error with the HTTP status code
                if response.status_code == 404:
                    raise QuestradeGeneralError("1001", "Invalid endpoint", 404)
                elif response.status_code == 400:
                    # Try to extract error message from response text
                    error_message = response.text.strip()
                    if "Invalid or malformed argument" in error_message:
                        raise QuestradeGeneralError("1002", error_message, 400)
                    else:
                        raise QuestradeGeneralError("1002", "Invalid or malformed argument", 400)
                else:
                    raise QuestradeGeneralError("1021", f"HTTP Error {response.status_code}: {response.text}", response.status_code)
                
        except requests.exceptions.ConnectionError as e:
            raise QuestradeGeneralError("1011", f"Connection error: {str(e)}", None)
        
        except requests.exceptions.Timeout as e:
            raise QuestradeGeneralError("1011", f"Request timed out: {str(e)}", None)
        
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                try:
                    error_data = e.response.json()
                    if 'code' in error_data and 'message' in error_data:
                        # Use the API's error code and message directly
                        error_code = str(error_data.get('code'))
                        error_message = error_data.get('message')
                        
                        if 'orderId' in error_data and 'orders' in error_data:
                            order_id = error_data.get('orderId')
                            orders = error_data.get('orders', [])
                            raise QuestradeOrderError(error_code, error_message, order_id, orders, status_code)
                        else:
                            raise QuestradeGeneralError(error_code, error_message, status_code)
                except (ValueError, json.JSONDecodeError):
                    pass
            
            # If we couldn't extract structured error info from the response, use a general error
            raise QuestradeGeneralError("1021", f"Request exception: {str(e)}", getattr(e, 'response', {}).get('status_code'))
        
        except json.JSONDecodeError as e:
            raise QuestradeGeneralError("1010", f"Invalid JSON response: {str(e)}", None)
        
        except Exception as e:
            # If the exception is already a QuestradeAPIError, don't wrap it
            if isinstance(e, QuestradeAPIError):
                raise
            else:
                raise QuestradeGeneralError("1021", f"Unexpected error: {str(e)}", None)
    
    # Account endpoints
    def get_accounts(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all accounts associated with the user.
        
        Returns:
            Dict containing:
                accounts (List[Dict]): List of account records with:
                    type (str): Account type (e.g., 'Margin', 'TFSA', 'RRSP')
                    number (str): Account number
                    status (str): Account status (e.g., 'Active')
                    isPrimary (bool): Whether this is the primary account
                    isBilling (bool): Whether this is the billing account
                    clientAccountType (str): Client account type
        """
        return self._make_request('v1/accounts')
    
    def get_account_positions(self, account_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get positions for a specific account.
        
        Args:
            account_id (str): Account number to retrieve positions for
            
        Returns:
            Dict containing:
                positions (List[Dict]): List of position records with:
                    symbol (str): Position symbol
                    symbolId (int): Internal symbol identifier 
                    openQuantity (float): Position quantity remaining open
                    closedQuantity (float): Portion of position closed today
                    currentMarketValue (float): Market value of position
                    currentPrice (float): Current price of position symbol
                    averageEntryPrice (float): Average price paid for position
                    closedPnL (float): Realized profit/loss
                    openPnL (float): Unrealized profit/loss
                    totalCost (float): Total cost of the position
                    isRealTime (bool): If real-time quote used for PnL
                    isUnderReorg (bool): If symbol undergoing reorganization
        """
        return self._make_request(f'v1/accounts/{account_id}/positions')
    
    def get_account_balances(self, account_id: str) -> Dict[str, Dict[str, Any]]:
        """Get balances for a specific account.
        
        Args:
            account_id (str): Account number to retrieve balances for
            
        Returns:
            Dict containing:
                perCurrencyBalances (List[Dict]): List of balances per currency:
                    currency (str): Currency code
                    cash (float): Cash balance
                    marketValue (float): Market value
                    totalEquity (float): Total equity
                    buyingPower (float): Buying power
                    maintenanceExcess (float): Maintenance excess
                    isRealTime (bool): Whether values are real-time
                combinedBalances (List[Dict]): List of combined balances:
                    currency (str): Currency code
                    cash (float): Cash balance
                    marketValue (float): Market value
                    totalEquity (float): Total equity
                    buyingPower (float): Buying power
                    maintenanceExcess (float): Maintenance excess
                    isRealTime (bool): Whether values are real-time
                sodPerCurrencyBalances (List[Dict]): Start-of-day balances per currency
                sodCombinedBalances (List[Dict]): Start-of-day combined balances
        """
        return self._make_request(f'v1/accounts/{account_id}/balances')
    
    def get_account_executions(self, account_id: str, start_time: Optional[str] = None, 
                              end_time: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get executions for a specific account.
        
        Args:
            account_id (str): Account number to retrieve executions for
            start_time (str, optional): Start time for filtering executions (ISO format)
            end_time (str, optional): End time for filtering executions (ISO format)
            
        Returns:
            Dict containing:
                executions (List[Dict]): List of execution records with:
                    symbol (str): Symbol that was traded
                    symbolId (int): Internal symbol identifier
                    quantity (float): Quantity that was executed
                    side (str): Side of the execution (e.g., 'Buy', 'Sell')
                    price (float): Price at which the execution occurred
                    id (int): Execution identifier
                    orderId (int): Order identifier
                    orderChainId (int): Order chain identifier
                    exchangeExecId (str): Exchange execution identifier
                    timestamp (str): Time at which execution occurred
                    notes (str): Notes on the execution
                    venue (str): Venue where the execution occurred
                    totalCost (float): Total cost of the execution
                    orderPlacementCommission (float): Commission for order placement
                    commission (float): Commission for the execution
                    executionFee (float): Fee for the execution
                    secFee (float): SEC fee
                    canadianExecutionFee (float): Canadian execution fee
                    parentId (int): Parent order identifier
        """
        params = {}
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return self._make_request(f'v1/accounts/{account_id}/executions', params=params)
    
    def get_account_orders(self, account_id: str, start_time: Optional[str] = None, 
                          end_time: Optional[str] = None, state: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get orders for a specific account.
        
        Args:
            account_id (str): Account number to retrieve orders for
            start_time (str, optional): Start time for filtering orders (ISO format)
            end_time (str, optional): End time for filtering orders (ISO format)
            state (str, optional): State filter for orders (e.g., 'All', 'Open', 'Closed')
            
        Returns:
            Dict containing:
                orders (List[Dict]): List of order records with:
                    id (int): Order identifier
                    symbol (str): Symbol being ordered
                    symbolId (int): Internal symbol identifier
                    totalQuantity (float): Total quantity of the order
                    openQuantity (float): Remaining open quantity
                    filledQuantity (float): Filled quantity
                    canceledQuantity (float): Canceled quantity
                    side (str): Side of the order (e.g., 'Buy', 'Sell')
                    orderType (str): Type of order (e.g., 'Limit', 'Market')
                    limitPrice (float): Limit price for the order
                    stopPrice (float): Stop price for the order
                    isAllOrNone (bool): Whether the order is all-or-none
                    isAnonymous (bool): Whether the order is anonymous
                    icebergQty (float): Iceberg quantity
                    minQuantity (float): Minimum quantity
                    avgExecPrice (float): Average execution price
                    lastExecPrice (float): Last execution price
                    source (str): Source of the order
                    timeInForce (str): Time in force (e.g., 'Day', 'GoodTillCanceled')
                    gtdDate (str): Good-till-date
                    state (str): State of the order (e.g., 'Filled', 'Canceled')
                    clientReasonStr (str): Client reason string
                    chainId (int): Order chain identifier
                    creationTime (str): Time at which the order was created
                    updateTime (str): Time at which the order was last updated
                    notes (str): Notes on the order
                    primaryRoute (str): Primary route for the order
                    secondaryRoute (str): Secondary route for the order
                    orderRoute (str): Order route
                    venueHoldingOrder (str): Venue holding the order
                    comissionCharged (float): Commission charged
                    exchangeOrderId (str): Exchange order identifier
                    isSignificantShareHolder (bool): Whether the order is from a significant shareholder
                    isInsider (bool): Whether the order is from an insider
                    isLimitOffsetInDollar (bool): Whether the limit offset is in dollars
                    userId (int): User identifier
                    placementCommission (float): Placement commission
                    legs (List[Dict]): List of order legs for multi-leg orders
                    strategyType (str): Strategy type for the order
                    triggerStopPrice (float): Trigger stop price
                    orderGroupId (int): Order group identifier
                    orderClass (str): Order class
                    mainChainId (int): Main chain identifier
        """
        params = {}
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        if state:
            params['stateFilter'] = state
        
        return self._make_request(f'v1/accounts/{account_id}/orders', params=params)
    
    # Market data endpoints
    def get_symbols(self, symbols: List[str] = None, symbol_names: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get detailed information about one or more symbols.
        
        Args:
            symbols (List[str], optional): List of symbol IDs to retrieve
            symbol_names (List[str], optional): List of symbol names to retrieve
            
        Returns:
            Dict containing:
                symbols (List[Dict]): List of symbol records with:
                    symbol (str): Symbol that follows Questrade symbology (e.g., "TD.TO")
                    symbolId (int): Internal symbol identifier
                    prevDayClosePrice (float): Closing trade price from previous trading day
                    highPrice52 (float): 52-week high price
                    lowPrice52 (float): 52-week low price
                    averageVol3Months (int): Average trading volume over trailing 3 months
                    averageVol20Days (int): Average trading volume over trailing 20 days
                    outstandingShares (int): Total number of shares outstanding
                    eps (float): Trailing 12-month earnings per share
                    pe (float): Trailing 12-month price to earnings ratio
                    dividend (float): Dividend amount per share
                    yield (float): Dividend yield (dividend / prevDayClosePrice)
                    exDate (str): Dividend ex-date
                    marketCap (float): Market capitalization
                    tradeUnit (int): Trade unit size
                    optionType (str): Option type (e.g., "Call")
                    optionDurationType (str): Option duration type (e.g., "Weekly")
                    optionRoot (str): Option root symbol
                    optionContractDeliverables (Dict): Option contract deliverables containing:
                        underlyings (List[Dict]): List of underlying multiplier pairs with:
                            multiplier (int): Number of shares per contract
                            underlyingSymbol (str): Underlying symbol
                            underlyingSymbolId (str): Underlying symbol ID
                        cashInLieu (float): Cash in lieu amount per contract
                    optionExerciseType (str): Option exercise style (e.g., "American")
                    listingExchange (str): Primary listing exchange
                    description (str): Symbol description
                    securityType (str): Security type (e.g., "Stock")
                    optionExpiryDate (str): Option expiry date
                    dividendDate (str): Dividend declaration date
                    optionStrikePrice (float): Option strike price
                    isQuotable (bool): Whether the symbol is actively listed
                    hasOptions (bool): Whether the symbol is an underlying option
                    currency (str): Currency code (ISO format)
                    minTicks (List[Dict]): List of minimum tick data with:
                        pivot (float): Beginning of interval for min price increment
                        minTick (float): Minimum price increment
                    industrySector (str): Industry sector classification
                    industryGroup (str): Industry group classification 
                    industrySubGroup (str): Industry subgroup classification
                    
        Note: Either symbols or symbol_names must be provided, but not both.
        """
        if symbols and symbol_names:
            raise ValueError("Cannot specify both symbols and symbol_names")
        if not symbols and not symbol_names:
            raise ValueError("Must specify either symbols or symbol_names")
            
        params = {}
        if symbols:
            params['ids'] = ','.join(map(str, symbols))
        if symbol_names:
            params['names'] = ','.join(symbol_names)
            
        return self._make_request('v1/symbols', params=params)
    
    def search_symbols(self, prefix: str, offset: int = 0) -> Dict[str, List[Dict[str, Any]]]:
        """Search for symbols by prefix.
        
        Args:
            prefix (str): Symbol prefix to search for
            offset (int, optional): Offset for pagination
            
        Returns:
            Dict containing:
                symbols (List[Dict]): List of symbol records with:
                    symbol (str): Symbol
                    symbolId (int): Internal symbol identifier
                    description (str): Description of the symbol
                    securityType (str): Security type
                    listingExchange (str): Listing exchange
                    isQuotable (bool): Whether the symbol is quotable
                    isTradable (bool): Whether the symbol is tradable
                    currency (str): Currency of the symbol
        """
        return self._make_request('v1/symbols/search', params={'prefix': prefix, 'offset': offset})
    
    def get_symbol_options(self, symbol_id: str) -> Dict:
        """Get option chain for a symbol.
        
        Args:
            symbol_id (str): Symbol ID to retrieve option chain for
            
        Returns:
            Dict containing:
                options (List[Dict]): List of option chain elements per expiry date with:
                    expiryDate (str): Option expiry date
                    description (str): Description of the underlying option
                    listingExchange (str): Primary listing exchange
                    optionExerciseType (str): Option exercise style (e.g., "American")
                    chainPerRoot (List[Dict]): List of option chains per root with:
                        root (str): Option root symbol
                        chainPerStrikePrice (List[Dict]): List of strike prices with:
                            strikePrice (float): Option strike price
                            callSymbolId (int): Internal identifier of the call option
                            putSymbolId (int): Internal identifier of the put option
        """
        return self._make_request(f'v1/symbols/{symbol_id}/options')
    
    def get_markets(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get information about supported markets.
        
        Returns:
            Dict containing:
                markets (List[Dict]): List of market records with:
                    name (str): Market name
                    tradingVenues (List[str]): List of trading venue codes
                    defaultTradingVenue (str): Default trading venue code
                    primaryOrderRoutes (List[str]): List of primary order route codes
                    secondaryOrderRoutes (List[str]): List of secondary order route codes
                    level1Feeds (List[str]): List of level 1 market data feed codes
                    level2Feeds (List[str]): List of level 2 market data feed codes
                    extendedStartTime (str): Pre-market opening time for current trading date
                    startTime (str): Regular market opening time for current trading date
                    endTime (str): Regular market closing time for current trading date
                    extendedEndTime (str): Extended market closing time for current trading date
                    currency (str): Currency code (ISO format)
                    snapQuotesLimit (int): Number of snap quotes that can be retrieved
        """
        return self._make_request('v1/markets')
    
    def get_quotes(self, symbol_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Get real-time or delayed quotes for a list of symbols.
        
        Note: Real-time quotes require a real-time data package subscription. Without a subscription,
        quotes will be delayed once the snap quote limit is reached for a market.
        
        Args:
            symbol_ids (List[str]): List of internal symbol identifiers
            
        Returns:
            Dict containing:
                quotes (List[Dict]): List of quote records with:
                    symbol (str): Symbol name in Questrade format
                    symbolId (int): Internal symbol identifier
                    tier (str): Market tier
                    bidPrice (float): Bid price
                    bidSize (int): Bid quantity
                    askPrice (float): Ask price 
                    askSize (int): Ask quantity
                    lastTradePriceTrHrs (float): Last trade price during regular hours
                    lastTradePrice (float): Price of last trade
                    lastTradeSize (int): Quantity of last trade
                    lastTradeTick (str): Trade direction
                    lastTradeTime (str): Time of last trade
                    volume (int): Trading volume
                    openPrice (float): Opening price
                    highPrice (float): Daily high
                    lowPrice (float): Daily low
                    delay (bool): Whether quote is delayed vs real-time
                    isHalted (bool): Whether trading is halted
        """
        ids = ','.join(map(str, symbol_ids))
        return self._make_request('v1/markets/quotes', params={'ids': ids})
    
    def get_candles(self, symbol_id: str, start_time: str, end_time: str, 
                   interval: str = 'OneDay') -> Dict[str, Any]:
        """
        Get historical candles for a symbol.
        
        Args:
            symbol_id (str): Symbol ID
            start_time (str): Start time in ISO format with timezone (e.g., "2021-01-01T00:00:00.000000-05:00")
            end_time (str): End time in ISO format with timezone (e.g., "2021-01-31T00:00:00.000000-05:00")
            interval (str): Candle interval (OneMinute, TwoMinutes, ThreeMinutes, FourMinutes, FiveMinutes, 
                          TenMinutes, FifteenMinutes, TwentyMinutes, HalfHour, OneHour, TwoHours, FourHours, 
                          OneDay, OneWeek, OneMonth, OneYear)
                          
        Returns:
            Dict containing:
                candles (List[Dict]): List of candle records with:
                    start (str): Start time of the candle
                    end (str): End time of the candle
                    low (float): Low price during the candle period
                    high (float): High price during the candle period
                    open (float): Opening price of the candle period
                    close (float): Closing price of the candle period
                    volume (int): Volume traded during the candle period
        """
        # Ensure datetime has proper format with timezone
        if 'T' in start_time and not any(tz in start_time for tz in ['+', '-', 'Z']):
            # If datetime has no timezone, add Eastern timezone
            start_time = start_time.split('.')[0] + ".000000-05:00"
            
        if 'T' in end_time and not any(tz in end_time for tz in ['+', '-', 'Z']):
            # If datetime has no timezone, add Eastern timezone
            end_time = end_time.split('.')[0] + ".000000-05:00"
        
        params = {
            'startTime': start_time,
            'endTime': end_time,
            'interval': interval
        }
        return self._make_request(f'v1/markets/candles/{symbol_id}', params=params)
    
    def get_account_activities(self, account_id: str, start_time: Optional[str] = None, 
                              end_time: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get account activities for a specific account.
        
        Args:
            account_id (str): Account number to retrieve activities for
            start_time (str, optional): Start time for filtering activities (ISO format with timezone, e.g., "2021-01-01T00:00:00.000000-05:00")
            end_time (str, optional): End time for filtering activities (ISO format with timezone, e.g., "2021-01-31T00:00:00.000000-05:00")
            
        Returns:
            Dict containing:
                activities (List[Dict]): List of activity records with:
                    tradeDate (str): Date of the activity
                    transactionDate (str): Transaction date of the activity
                    settlementDate (str): Settlement date of the activity
                    action (str): Type of action (e.g., 'Buy', 'Sell', 'Dividend')
                    symbol (str): Symbol involved in the activity
                    symbolId (int): Internal symbol identifier
                    description (str): Description of the activity
                    currency (str): Currency of the activity
                    quantity (float): Quantity involved in the activity
                    price (float): Price at which the activity occurred
                    grossAmount (float): Gross amount of the activity
                    commission (float): Commission charge for the activity
                    netAmount (float): Net amount of the activity
                    type (str): Activity type
                    
        Note:
            The date parameters must include timezone information. 
            Maximum 31 days of data can be requested at a time.
        """
        params = {}
        if start_time:
            # Ensure datetime has proper format with timezone
            if 'T' in start_time and not any(tz in start_time for tz in ['+', '-', 'Z']):
                # If datetime has no timezone, add Eastern timezone
                start_time = start_time.split('.')[0] + ".000000-05:00"
            params['startTime'] = start_time
        if end_time:
            # Ensure datetime has proper format with timezone
            if 'T' in end_time and not any(tz in end_time for tz in ['+', '-', 'Z']):
                # If datetime has no timezone, add Eastern timezone
                end_time = end_time.split('.')[0] + ".000000-05:00"
            params['endTime'] = end_time
        
        return self._make_request(f'v1/accounts/{account_id}/activities', params=params)
    
    def get_time(self) -> Dict[str, str]:
        """Get current server time.
        
        Returns:
            Dict containing:
                time (str): Current server time in ISO format
        """
        return self._make_request('v1/time')
    
    def get_symbol(self, symbol_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get detailed information about a specific symbol.
        
        Args:
            symbol_id (str): Symbol ID to retrieve
            
        Returns:
            Dict containing:
                symbols (List[Dict]): List with a single symbol record with:
                    symbol (str): Symbol that follows Questrade symbology (e.g., "TD.TO")
                    symbolId (int): Internal symbol identifier
                    prevDayClosePrice (float): Closing trade price from previous trading day
                    highPrice52 (float): 52-week high price
                    lowPrice52 (float): 52-week low price
                    averageVol3Months (int): Average trading volume over trailing 3 months
                    averageVol20Days (int): Average trading volume over trailing 20 days
                    outstandingShares (int): Total number of shares outstanding
                    eps (float): Trailing 12-month earnings per share
                    pe (float): Trailing 12-month price to earnings ratio
                    dividend (float): Dividend amount per share
                    yield (float): Dividend yield (dividend / prevDayClosePrice)
                    exDate (str): Dividend ex-date
                    marketCap (float): Market capitalization
                    tradeUnit (int): Trade unit size
                    optionType (str): Option type (e.g., "Call")
                    optionDurationType (str): Option duration type (e.g., "Weekly")
                    optionRoot (str): Option root symbol
                    optionContractDeliverables (Dict): Option contract deliverables
                    optionExerciseType (str): Option exercise style (e.g., "American")
                    listingExchange (str): Primary listing exchange
                    description (str): Symbol description
                    securityType (str): Security type (e.g., "Stock")
                    optionExpiryDate (str): Option expiry date
                    dividendDate (str): Dividend declaration date
                    optionStrikePrice (float): Option strike price
                    isQuotable (bool): Whether the symbol is actively listed
                    hasOptions (bool): Whether the symbol is an underlying option
                    currency (str): Currency code (ISO format)
                    minTicks (List[Dict]): List of minimum tick data
                    industrySector (str): Industry sector classification
                    industryGroup (str): Industry group classification 
                    industrySubGroup (str): Industry subgroup classification
        """
        return self._make_request(f'v1/symbols/{symbol_id}')
    
    def get_quote(self, symbol_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get real-time or delayed quote for a single symbol.
        
        Args:
            symbol_id (str): Internal symbol identifier
            
        Returns:
            Dict containing:
                quotes (List[Dict]): List with a single quote record with:
                    symbol (str): Symbol name in Questrade format
                    symbolId (int): Internal symbol identifier
                    tier (str): Market tier
                    bidPrice (float): Bid price
                    bidSize (int): Bid quantity
                    askPrice (float): Ask price 
                    askSize (int): Ask quantity
                    lastTradePriceTrHrs (float): Last trade price during regular hours
                    lastTradePrice (float): Price of last trade
                    lastTradeSize (int): Quantity of last trade
                    lastTradeTick (str): Trade direction
                    lastTradeTime (str): Time of last trade
                    volume (int): Trading volume
                    openPrice (float): Opening price
                    highPrice (float): Daily high
                    lowPrice (float): Daily low
                    delay (bool): Whether quote is delayed vs real-time
                    isHalted (bool): Whether trading is halted
        """
        return self._make_request(f'v1/markets/quotes/{symbol_id}')
    
    def get_option_quotes(self, option_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Get quotes for a list of option symbols.
        
        Args:
            option_ids (List[str]): List of option symbol identifiers
            
        Returns:
            Dict containing:
                quotes (List[Dict]): List of option quote records with:
                    symbol (str): Option symbol 
                    symbolId (int): Internal symbol identifier
                    bidPrice (float): Bid price
                    bidSize (int): Bid quantity
                    askPrice (float): Ask price 
                    askSize (int): Ask quantity
                    lastTradePriceTrHrs (float): Last trade price during regular hours
                    lastTradePrice (float): Price of last trade
                    lastTradeSize (int): Quantity of last trade
                    lastTradeTick (str): Trade direction
                    lastTradeTime (str): Time of last trade
                    volume (int): Trading volume
                    openPrice (float): Opening price
                    highPrice (float): Daily high
                    lowPrice (float): Daily low
                    volatility (float): Implied volatility percentage
                    delta (float): Option delta greek
                    gamma (float): Option gamma greek
                    theta (float): Option theta greek
                    vega (float): Option vega greek
                    rho (float): Option rho greek
                    openInterest (int): Open interest
                    delay (bool): Whether quote is delayed vs real-time
                    isHalted (bool): Whether trading is halted
                    VWAP (float): Volume weighted average price
        """
        ids = ','.join(map(str, option_ids))
        return self._make_request('v1/markets/quotes/options', params={'optionIds': ids})
    
    def get_strategy_quotes(self, variant_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get quotes for a strategy (multi-leg orders).
        
        Args:
            variant_id (str): Strategy variant identifier
            
        Returns:
            Dict containing:
                quotes (List[Dict]): List of strategy quote records
        """
        return self._make_request('v1/markets/quotes/strategies', params={'variantId': variant_id})
    
