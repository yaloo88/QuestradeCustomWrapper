"""
Rate Limiting Module for Questrade API

This module provides a rate limiter that enforces Questrade API rate limits.
It tracks requests across different API categories and ensures limits are not exceeded.
"""

import time
import threading
from enum import Enum
from typing import Dict, Optional
from collections import deque


class ApiCategory(Enum):
    """Categories of API calls for rate limiting."""
    ACCOUNT = "account"    # Account-related calls
    MARKET = "market"      # Market data calls


class RateLimiter:
    """
    Rate limiter for Questrade API that enforces per-second and per-hour limits.
    
    The Questrade API has the following rate limits:
    - Account calls: 30 requests/second, 30,000 requests/hour
    - Market data calls: 20 requests/second, 15,000 requests/hour
    """
    
    # Define rate limits per category (requests per second, requests per hour)
    RATE_LIMITS = {
        ApiCategory.ACCOUNT: (30, 30000),
        ApiCategory.MARKET: (20, 15000),
    }
    
    def __init__(self):
        """Initialize the rate limiter."""
        # Initialize request history for each category
        # We'll track both per-second and per-hour requests
        self._lock = threading.RLock()
        self._request_history: Dict[ApiCategory, Dict[str, deque]] = {}
        
        # Initialize request history for each category
        for category in ApiCategory:
            self._request_history[category] = {
                'second': deque(maxlen=self.RATE_LIMITS[category][0]),
                'hour': deque(maxlen=self.RATE_LIMITS[category][1])
            }
            
        # Track remaining requests from response headers
        self._remaining: Dict[ApiCategory, int] = {
            ApiCategory.ACCOUNT: self.RATE_LIMITS[ApiCategory.ACCOUNT][0],
            ApiCategory.MARKET: self.RATE_LIMITS[ApiCategory.MARKET][0]
        }
        
        # Track when limits reset (Unix timestamp)
        self._reset_time: Dict[ApiCategory, float] = {
            ApiCategory.ACCOUNT: time.time() + 1,  # 1 second default
            ApiCategory.MARKET: time.time() + 1
        }
    
    def update_limits(self, category: ApiCategory, remaining: int, reset_time: float):
        """
        Update rate limit information from API response headers.
        
        Args:
            category: The API category
            remaining: Value from X-RateLimit-Remaining header
            reset_time: Value from X-RateLimit-Reset header
        """
        with self._lock:
            self._remaining[category] = remaining
            self._reset_time[category] = reset_time
    
    def record_request(self, category: ApiCategory):
        """
        Record that an API request was made for the specified category.
        
        Args:
            category: The API category the request belongs to
        """
        current_time = time.time()
        
        with self._lock:
            # Record the request timestamp for both per-second and per-hour tracking
            self._request_history[category]['second'].append(current_time)
            self._request_history[category]['hour'].append(current_time)
    
    def wait_if_needed(self, category: ApiCategory) -> float:
        """
        Check if we need to wait before making another request.
        
        Args:
            category: The API category the request belongs to
            
        Returns:
            float: The number of seconds to wait (0 if no wait needed)
        """
        with self._lock:
            current_time = time.time()
            
            # Check if we need to wait based on server-provided limits
            if self._remaining[category] <= 0:
                wait_time = max(0, self._reset_time[category] - current_time)
                if wait_time > 0:
                    return wait_time
            
            # Also check our local tracking for per-second limit
            second_limit, hour_limit = self.RATE_LIMITS[category]
            second_history = self._request_history[category]['second']
            hour_history = self._request_history[category]['hour']
            
            # If we've reached the per-second limit, calculate wait time
            if len(second_history) >= second_limit:
                oldest = second_history[0]
                wait_time = max(0, 1.0 - (current_time - oldest))
                if wait_time > 0:
                    return wait_time
            
            # If we've reached the per-hour limit, calculate wait time
            if len(hour_history) >= hour_limit:
                oldest = hour_history[0]
                wait_time = max(0, 3600.0 - (current_time - oldest))
                if wait_time > 0:
                    return wait_time
                
            # No wait needed
            return 0
    
    def get_category_for_endpoint(self, endpoint: str) -> ApiCategory:
        """
        Determine the API category for a given endpoint.
        
        Args:
            endpoint: The API endpoint
            
        Returns:
            ApiCategory: The category the endpoint belongs to
        """
        # Classify the endpoint into a category based on the URL
        endpoint = endpoint.lstrip('/')
        
        # Market data calls
        if (endpoint.startswith('v1/markets') or 
            endpoint.startswith('v1/symbols') or 
            (endpoint.startswith('v1/symbols/') and '/options' in endpoint)):
            return ApiCategory.MARKET
        
        # Account calls (includes time endpoint)
        return ApiCategory.ACCOUNT 