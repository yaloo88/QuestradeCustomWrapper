# Questrade API Validation Scripts

This directory contains scripts for validating that all methods in the Questrade API wrapper are functioning correctly.

## Scripts

- `api_validator.py` - The main validator class that tests all API methods
- `run_validator.py` - A simple wrapper script to run the validator with nice output formatting

## Usage

To validate all API methods:

```bash
# From the project root directory
python scripts/run_validator.py
```

## Results

The validator will:

1. Attempt to call each API method in the wrapper
2. Print the results of each test (pass, fail, or skip)
3. Print a summary of all tests
4. Save detailed results to a JSON file in the `validation_results` directory

## Expected Output

```
========================================================================
                       QUESTRADE API VALIDATOR                        
            Verifying all API methods are functioning correctly          
========================================================================

Starting Questrade API validation...

🧪 Testing: Authentication...
✅ PASSED: Authentication
🧪 Testing: Get Time...
✅ PASSED: Get Time
...

========================================================================
VALIDATION SUMMARY: 16 tests
  ✅ Passed:  14
  ❌ Failed:  0
  ⏭️  Skipped: 2
========================================================================

Results written to validation_results/api_validation_20230615_120145.json
```

## Return Codes

- `0`: All tests passed or were skipped
- `1`: One or more tests failed
- `130`: Validator was stopped by user (Ctrl+C) 