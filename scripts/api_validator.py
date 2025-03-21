#!/usr/bin/env python
"""
Questrade API Validation Script

This script tests all methods of the QuestradeAPI wrapper to verify they are working correctly.
It attempts to call each API endpoint and reports success or failure.
"""

import os
import sys
from pathlib import Path
import datetime
import time
import json
from typing import Dict, List, Any, Callable

# Add project root to path
project_root = Path(__file__).parent.parent.resolve()
sys.path.append(str(project_root))

from QuestradeAPI.CustomWrapper import QuestradeAPI

class APIValidator:
    """Class to validate all API methods in the QuestradeAPI wrapper."""
    
    def __init__(self):
        """Initialize the validator with a QuestradeAPI instance."""
        self.api = QuestradeAPI()
        self.results = {
            "passed": [],
            "failed": [],
            "skipped": []
        }
        self.account_id = None
        self.symbol_id = None
        self.option_ids = []
        
    def run_test(self, test_name: str, test_function: Callable, skip_reason: str = None) -> bool:
        """Run a test and record the result.
        
        Args:
            test_name: Name of the test
            test_function: Function to run for the test
            skip_reason: Reason to skip the test, if any
            
        Returns:
            bool: True if test passed or was skipped, False if it failed
        """
        if skip_reason:
            print(f"⏭️  SKIPPED: {test_name} - {skip_reason}")
            self.results["skipped"].append({"name": test_name, "reason": skip_reason})
            return True
            
        print(f"🧪 Testing: {test_name}...")
        try:
            result = test_function()
            print(f"✅ PASSED: {test_name}")
            self.results["passed"].append({"name": test_name, "data": str(result)[:100] + "..." if result else None})
            return True
        except Exception as e:
            print(f"❌ FAILED: {test_name} - {str(e)}")
            self.results["failed"].append({"name": test_name, "error": str(e)})
            return False

    def validate_all(self):
        """Run all validation tests."""
        print("Starting Questrade API validation...\n")
        
        # Test authentication
        self.run_test("Authentication", lambda: self.api.authenticate())
        
        # Test time endpoint
        self.run_test("Get Time", lambda: self.api.get_time())
        
        # Test rate limiting
        self.run_test("Rate Limiting", self._test_rate_limiting)
        
        # Test account endpoints
        accounts_result = self.run_test("Get Accounts", lambda: self.api.get_accounts())
        
        if accounts_result and len(self.api.get_accounts().get('accounts', [])) > 0:
            self.account_id = self.api.get_accounts()['accounts'][0]['number']
            print(f"\nUsing account ID: {self.account_id} for account-specific tests\n")
            
            # Test account-specific endpoints
            self.run_test("Get Account Balances", lambda: self.api.get_account_balances(self.account_id))
            self.run_test("Get Account Positions", lambda: self.api.get_account_positions(self.account_id))
            self.run_test("Get Account Activities", lambda: self.api.get_account_activities(
                self.account_id, 
                start_time=(datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S.000000-05:00"),
                end_time=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
            ))
            self.run_test("Get Account Orders", lambda: self.api.get_account_orders(self.account_id))
            self.run_test("Get Account Executions", lambda: self.api.get_account_executions(self.account_id))
        else:
            print("\nNo accounts found, skipping account-specific tests\n")
            
        # Test market endpoints
        self.run_test("Get Markets", lambda: self.api.get_markets())
        
        # Test symbol endpoints
        search_result = self.run_test("Search Symbols", lambda: self.api.search_symbols("AAPL"))
        
        if search_result and len(self.api.search_symbols("AAPL").get('symbols', [])) > 0:
            self.symbol_id = self.api.search_symbols("AAPL")['symbols'][0]['symbolId']
            symbol_name = self.api.search_symbols("AAPL")['symbols'][0]['symbol']
            print(f"\nUsing symbol: {symbol_name} (ID: {self.symbol_id}) for symbol-specific tests\n")
            
            # Test symbol-specific endpoints
            self.run_test("Get Symbol", lambda: self.api.get_symbol(self.symbol_id))
            self.run_test("Get Symbol Options", lambda: self.api.get_symbol_options(self.symbol_id))
            self.run_test("Get Quote", lambda: self.api.get_quote(self.symbol_id))
            
            # Test candles endpoint
            start_time = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
            end_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000000-05:00")
            self.run_test("Get Candles", lambda: self.api.get_candles(
                self.symbol_id, start_time, end_time, interval='OneDay'
            ))
            
            # Try to get option symbols for option quote test
            try:
                options_data = self.api.get_symbol_options(self.symbol_id)
                if options_data and 'options' in options_data and len(options_data['options']) > 0:
                    for option_chain in options_data['options'][:1]:  # Just use the first expiry date
                        if 'chainPerRoot' in option_chain and len(option_chain['chainPerRoot']) > 0:
                            for root in option_chain['chainPerRoot'][:1]:
                                if 'chainPerStrikePrice' in root and len(root['chainPerStrikePrice']) > 0:
                                    for strike in root['chainPerStrikePrice'][:2]:  # Get a couple of strikes
                                        if 'callSymbolId' in strike:
                                            self.option_ids.append(strike['callSymbolId'])
                                        if 'putSymbolId' in strike:
                                            self.option_ids.append(strike['putSymbolId'])
                                        if len(self.option_ids) >= 2:  # Just need a couple for testing
                                            break
                                if len(self.option_ids) >= 2:
                                    break
                        if len(self.option_ids) >= 2:
                            break
                
                if self.option_ids:
                    print(f"\nFound option IDs: {self.option_ids} for options tests\n")
                    self.run_test("Get Option Quotes", lambda: self.api.get_option_quotes(self.option_ids))
                else:
                    self.run_test("Get Option Quotes", None, 
                                 "No option IDs found for the selected symbol")
            except Exception as e:
                print(f"Error getting option symbols: {e}")
                self.run_test("Get Option Quotes", None, 
                             f"Failed to get option IDs: {str(e)}")
        else:
            print("\nFailed to find symbol, skipping symbol-specific tests\n")
            
        # Test other endpoints that don't require specific IDs
        self.run_test("Get Symbols by Names", lambda: self.api.get_symbols(symbol_names=["AAPL", "MSFT"]))
        
        # Test strategy quotes - this requires a variant ID which is difficult to obtain automatically
        self.run_test("Get Strategy Quotes", None, 
                     "Requires a strategy variant ID which cannot be obtained automatically")
        
        # Print summary
        self.print_summary()
        
        # Write results to file
        self.write_results()

    def _test_rate_limiting(self):
        """Test that the rate limiting functionality works correctly."""
        from QuestradeAPI.CustomWrapper import QuestradeRateLimitError
        
        # Save the original rate limiting settings
        original_enforce_rate_limit = self.api.enforce_rate_limit
        original_max_retries = self.api.max_retries
        
        try:
            # Enable rate limiting with 0 retries for testing purposes
            self.api.enforce_rate_limit = True
            self.api.max_retries = 0
            
            # Make a large number of requests to the same endpoint to trigger rate limiting
            num_requests = 40  # This should exceed the per-second limit for account endpoints (30)
            
            # Get the API category for the time endpoint
            category = self.api.rate_limiter.get_category_for_endpoint('v1/time')
            
            # Fill the rate limiter history to simulate hitting the limit
            for _ in range(self.api.rate_limiter.RATE_LIMITS[category][0]):
                self.api.rate_limiter.record_request(category)
            
            # The next request should raise a rate limit error
            try:
                result = self.api.get_time()
                return False  # If we get here, rate limiting didn't work
            except QuestradeRateLimitError as e:
                # This is what we want - rate limiting worked
                if e.code == "1006" and e.status_code == 429:
                    return True
                return False  # Wrong error
            
        finally:
            # Restore the original settings
            self.api.enforce_rate_limit = original_enforce_rate_limit
            self.api.max_retries = original_max_retries

    def print_summary(self):
        """Print a summary of test results."""
        total = len(self.results["passed"]) + len(self.results["failed"]) + len(self.results["skipped"])
        
        print("\n" + "="*80)
        print(f"VALIDATION SUMMARY: {total} tests")
        print(f"  ✅ Passed:  {len(self.results['passed'])}")
        print(f"  ❌ Failed:  {len(self.results['failed'])}")
        print(f"  ⏭️  Skipped: {len(self.results['skipped'])}")
        print("="*80)
        
        if self.results["failed"]:
            print("\nFailed tests:")
            for test in self.results["failed"]:
                print(f"  - {test['name']}: {test['error']}")
        
        if self.results["skipped"]:
            print("\nSkipped tests:")
            for test in self.results["skipped"]:
                print(f"  - {test['name']}: {test['reason']}")
                
        print("\n")
        
    def write_results(self):
        """Write test results to a JSON file."""
        output_dir = os.path.join(project_root, "validation_results")
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"api_validation_{timestamp}.json")
        
        # Add summary stats
        results_with_summary = {
            "summary": {
                "total": len(self.results["passed"]) + len(self.results["failed"]) + len(self.results["skipped"]),
                "passed": len(self.results["passed"]),
                "failed": len(self.results["failed"]),
                "skipped": len(self.results["skipped"]),
                "timestamp": timestamp
            },
            "results": self.results
        }
        
        with open(output_file, 'w') as f:
            json.dump(results_with_summary, f, indent=2)
            
        print(f"Results written to {output_file}")

if __name__ == "__main__":
    validator = APIValidator()
    validator.validate_all() 