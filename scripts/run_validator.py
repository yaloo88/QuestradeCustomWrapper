#!/usr/bin/env python
"""
Run the Questrade API validator.

This script is a simple wrapper around the API validator that includes
error handling and a clean output format.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.resolve()
sys.path.append(str(project_root))

def main():
    """Run the API validator."""
    try:
        from scripts.api_validator import APIValidator
        
        print("\n" + "="*80)
        print("QUESTRADE API VALIDATOR".center(80))
        print("Verifying all API methods are functioning correctly".center(80))
        print("="*80 + "\n")
        
        validator = APIValidator()
        validator.validate_all()
        
        # Return code based on whether all tests passed
        if validator.results["failed"]:
            return 1
        return 0
        
    except ImportError as e:
        print(f"Error importing validator: {e}")
        print("Make sure you're running this script from the project root directory.")
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nValidator stopped by user.")
        sys.exit(130) 