#!/usr/bin/env python
"""
Test script to verify that the Chronos class can be imported correctly.
"""

import sys
import os

# Print Python path to identify where modules are being imported from
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print("\nPython path:")
for path in sys.path:
    print(f"  {path}")

print("\nAttempting to import Chronos...")
try:
    from QuestradeAPI import QuestradeAPI, Chronos
    print("\nImport successful!")
    print(f"Chronos module location: {Chronos.__module__}")
    print(f"QuestradeAPI package location: {QuestradeAPI.__module__}")
    
    # Create an instance to verify it works
    api = QuestradeAPI()
    chronos = Chronos(api=api)
    print("\nSuccessfully created Chronos instance.")
    print(f"Project root: {chronos.project_root}")
    
except ImportError as e:
    print(f"\nImport error: {e}")
    
    # Try to find the module
    print("\nSearching for Chronos module...")
    for path in sys.path:
        chronos_path = os.path.join(path, "QuestradeAPI", "Chronos.py")
        init_path = os.path.join(path, "QuestradeAPI", "__init__.py")
        
        if os.path.exists(chronos_path):
            print(f"  Found Chronos.py at: {chronos_path}")
            # Check if it's imported in __init__.py
            if os.path.exists(init_path):
                with open(init_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "from .Chronos import Chronos" in content:
                        print(f"  __init__.py imports Chronos")
                    else:
                        print(f"  __init__.py DOES NOT import Chronos")
        
except Exception as e:
    print(f"\nOther error: {e}")

print("\nTest complete.") 