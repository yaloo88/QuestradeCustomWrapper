#!/usr/bin/env python3
"""
Questrade API Error Handling Example

This script demonstrates how to handle the different types of errors
that can occur when using the Questrade API wrapper.
"""

import sys
import os
import datetime
from pathlib import Path

# Add the parent directory to the path so we can import the QuestradeAPI module
sys.path.append(str(Path(__file__).parent.parent))

from QuestradeAPI.CustomWrapper import QuestradeAPI, QuestradeAPIError, QuestradeGeneralError, QuestradeOrderError

def print_section(title):
    """Print a section title with formatting."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def demonstrate_error_handling():
    """Run examples of error handling scenarios."""
    print_section("Questrade API Error Handling Examples")
    
    # Initialize the API
    try:
        api = QuestradeAPI()
        print("✓ API initialized successfully\n")
    except Exception as e:
        print(f"✗ Failed to initialize API: {e}\n")
        return
    
    # Example 1: Invalid endpoint (General Error)
    print_section("Example 1: Invalid Endpoint (General Error)")
    try:
        print("Attempting to access invalid endpoint...")
        result = api._make_request('v1/invalid/endpoint')
        print("This should not be printed as the request should fail")
    except QuestradeGeneralError as e:
        print(f"✓ Caught QuestradeGeneralError as expected")
        print(f"  Error Code: {e.code}")
        print(f"  Error Message: {e.message}")
        print(f"  HTTP Status: {e.status_code}")
    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")
    
    # Example 2: Invalid parameter (General Error)
    print_section("Example 2: Invalid Parameter (General Error)")
    try:
        print("Attempting to get candles with invalid interval...")
        result = api.get_candles(
            symbol_id="9001",  # This might need to be updated to a valid symbol ID
            start_time=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000000-05:00"),
            end_time=(datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.000000-05:00"),
            interval="InvalidInterval"  # Invalid interval
        )
        print("This should not be printed as the request should fail")
    except QuestradeGeneralError as e:
        print(f"✓ Caught QuestradeGeneralError as expected")
        print(f"  Error Code: {e.code}")
        print(f"  Error Message: {e.message}")
        print(f"  HTTP Status: {e.status_code}")
    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")
    
    # Example 3: Invalid authentication token (simulate by temporarily corrupting token)
    print_section("Example 3: Invalid Authentication Token")
    
    # Save the original token
    original_token = api.refresh_token
    try:
        print("Simulating an invalid token...")
        api.refresh_token = "invalid_token"
        api.access_token = "invalid_access_token"
        
        # Try to make a request
        result = api.get_time()
        print("This should not be printed as the request should fail")
    except QuestradeAPIError as e:
        print(f"✓ Caught QuestradeAPIError as expected")
        print(f"  Error Code: {e.code}")
        print(f"  Error Message: {e.message}")
        print(f"  HTTP Status: {e.status_code}")
    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")
    finally:
        # Restore the original token
        api.refresh_token = original_token
        # Reauthenticate to fix the API state
        api.authenticate()
    
    # Example 4: Demonstrate how to handle both error types
    print_section("Example 4: Handling Different Error Types")
    try:
        print("Making another request to test proper error handling...")
        # This could be any API call that might fail
        result = api.get_time()
        print(f"✓ Request successful: {result}")
    except QuestradeOrderError as e:
        # Handle order errors (would occur in trading requests)
        print(f"Order Error: {e.code} - {e.message}")
        print(f"Order ID: {e.order_id}")
        print(f"Orders: {e.orders}")
    except QuestradeGeneralError as e:
        # Handle general errors
        print(f"General Error: {e.code} - {e.message}")
        print(f"HTTP Status: {e.status_code}")
    except Exception as e:
        # Handle any other unexpected errors
        print(f"Unexpected Error: {type(e).__name__} - {e}")
    
    print_section("End of Error Handling Examples")
    print("Examples completed. The error handling was demonstrated successfully.")

if __name__ == "__main__":
    try:
        demonstrate_error_handling()
    except Exception as e:
        print(f"\nUnexpected error running examples: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nExamples stopped by user.")
        sys.exit(130) 