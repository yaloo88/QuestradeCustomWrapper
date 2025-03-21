#!/usr/bin/env python3
"""
Questrade API Rate Limiting Example

This script demonstrates how the rate limiting functionality in the Questrade API wrapper works.
It makes rapid requests to show how the rate limiter prevents exceeding the API limits.
"""

import sys
import os
import time
import datetime
from pathlib import Path

# Add the parent directory to the path so we can import the QuestradeAPI module
sys.path.append(str(Path(__file__).parent.parent))

from QuestradeAPI.CustomWrapper import QuestradeAPI, QuestradeRateLimitError

def print_section(title):
    """Print a section title with formatting."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def format_time(seconds):
    """Format seconds into a human-readable string."""
    if seconds < 1:
        return f"{seconds*1000:.2f} ms"
    else:
        return f"{seconds:.2f} s"

def demonstrate_rate_limiting():
    """Run examples of rate limiting functionality."""
    print_section("Questrade API Rate Limiting Examples")
    
    # Initialize the API with rate limiting enabled
    try:
        api = QuestradeAPI(enforce_rate_limit=True, max_retries=3)
        print("✓ API initialized successfully with rate limiting enabled\n")
    except Exception as e:
        print(f"✗ Failed to initialize API: {e}\n")
        return
    
    # Example 1: Account endpoints (30 requests/second limit)
    print_section("Example 1: Account Endpoint Rate Limiting")
    
    print("Making 35 rapid requests to the time endpoint (limit is 30/second)...")
    start_time = time.time()
    
    results = []
    for i in range(35):
        loop_start = time.time()
        try:
            # Get the server time (this is an account endpoint)
            result = api.get_time()
            elapsed = time.time() - loop_start
            results.append((True, elapsed, None))
            print(f"  Request {i+1}: ✓ Success - Took {format_time(elapsed)}")
        except QuestradeRateLimitError as e:
            elapsed = time.time() - loop_start
            results.append((False, elapsed, e))
            print(f"  Request {i+1}: ✗ Rate Limited - Took {format_time(elapsed)}")
            print(f"    Error: {e}")
        except Exception as e:
            elapsed = time.time() - loop_start
            results.append((False, elapsed, e))
            print(f"  Request {i+1}: ✗ Error - Took {format_time(elapsed)}")
            print(f"    Error: {e}")
    
    total_time = time.time() - start_time
    success_count = sum(1 for r in results if r[0])
    
    print(f"\nCompleted {success_count} out of {len(results)} requests in {format_time(total_time)}")
    print(f"Average time per request: {format_time(total_time / len(results))}")
    
    # Example 2: Market data endpoints (20 requests/second limit)
    print_section("Example 2: Market Data Endpoint Rate Limiting")
    
    print("Making 25 rapid requests to the markets endpoint (limit is 20/second)...")
    start_time = time.time()
    
    results = []
    for i in range(25):
        loop_start = time.time()
        try:
            # Get the markets (this is a market data endpoint)
            result = api.get_markets()
            elapsed = time.time() - loop_start
            results.append((True, elapsed, None))
            print(f"  Request {i+1}: ✓ Success - Took {format_time(elapsed)}")
        except QuestradeRateLimitError as e:
            elapsed = time.time() - loop_start
            results.append((False, elapsed, e))
            print(f"  Request {i+1}: ✗ Rate Limited - Took {format_time(elapsed)}")
            print(f"    Error: {e}")
        except Exception as e:
            elapsed = time.time() - loop_start
            results.append((False, elapsed, e))
            print(f"  Request {i+1}: ✗ Error - Took {format_time(elapsed)}")
            print(f"    Error: {e}")
    
    total_time = time.time() - start_time
    success_count = sum(1 for r in results if r[0])
    
    print(f"\nCompleted {success_count} out of {len(results)} requests in {format_time(total_time)}")
    print(f"Average time per request: {format_time(total_time / len(results))}")
    
    # Example 3: Disabling rate limiting
    print_section("Example 3: Disabling Rate Limiting")
    
    # Create a new API instance with rate limiting disabled
    api_no_limits = QuestradeAPI(enforce_rate_limit=False)
    
    print("Making 10 rapid requests with rate limiting disabled...")
    start_time = time.time()
    
    results = []
    for i in range(10):
        loop_start = time.time()
        try:
            # Get the server time
            result = api_no_limits.get_time()
            elapsed = time.time() - loop_start
            results.append((True, elapsed, None))
            print(f"  Request {i+1}: ✓ Success - Took {format_time(elapsed)}")
        except Exception as e:
            elapsed = time.time() - loop_start
            results.append((False, elapsed, e))
            print(f"  Request {i+1}: ✗ Error - Took {format_time(elapsed)}")
            print(f"    Error: {e}")
        
        # Small sleep to avoid actually hitting the API limit
        time.sleep(0.05)
    
    total_time = time.time() - start_time
    success_count = sum(1 for r in results if r[0])
    
    print(f"\nCompleted {success_count} out of {len(results)} requests in {format_time(total_time)}")
    print(f"Average time per request: {format_time(total_time / len(results))}")
    print("\nNote: With rate limiting disabled, you might hit actual API rate limits.")
    print("In a production environment, it's recommended to keep rate limiting enabled.")
    
    print_section("End of Rate Limiting Examples")
    print("Examples completed. The rate limiting was demonstrated successfully.")

if __name__ == "__main__":
    try:
        demonstrate_rate_limiting()
    except Exception as e:
        print(f"\nUnexpected error running examples: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nExamples stopped by user.")
        sys.exit(130) 