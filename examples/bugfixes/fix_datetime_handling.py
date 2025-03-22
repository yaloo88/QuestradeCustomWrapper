#!/usr/bin/env python
"""
Fix the datetime handling issue in the Chronos.py file.
The issue is related to comparing offset-naive and offset-aware datetimes.
"""

import os
from pathlib import Path

def fix_chronos_file():
    """Fix the datetime handling in the Chronos.py file."""
    # Path to the Chronos.py file
    chronos_path = Path("QuestradeAPI") / "Chronos.py"
    
    if not chronos_path.exists():
        print(f"Error: {chronos_path} not found.")
        return
    
    # Read the file content
    with open(chronos_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Find and replace the problematic code
    # Target the specific line where the timezone-aware and timezone-naive datetimes are compared
    old_code = "                last_end_dt = datetime.fromisoformat(last_end.replace('Z', '+00:00'))\n                days_diff = (end_time - last_end_dt).days"
    new_code = """                # Convert the datetime from string ensuring both are timezone-aware
                try:
                    # Try to parse the datetime with timezone info
                    last_end_dt = datetime.fromisoformat(last_end.replace('Z', '+00:00'))
                    
                    # Make sure end_time is also timezone-aware if last_end_dt is
                    if last_end_dt.tzinfo is not None and end_time.tzinfo is None:
                        # Apply the same timezone as last_end_dt
                        end_time = end_time.replace(tzinfo=last_end_dt.tzinfo)
                    elif last_end_dt.tzinfo is None and end_time.tzinfo is not None:
                        # Apply the same timezone as end_time
                        last_end_dt = last_end_dt.replace(tzinfo=end_time.tzinfo)
                    
                    days_diff = (end_time - last_end_dt).days
                except (ValueError, TypeError) as e:
                    print(f"Error handling datetime: {e}")
                    # If there's an error, assume we need new data
                    days_diff = 1"""
    
    # Replace the code
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("Successfully found and replaced the problematic code.")
    else:
        print("Could not find the exact code to replace.")
        print("Trying with a more flexible search...")
        
        # Try to find the line with 'last_end_dt = datetime.fromisoformat'
        import re
        match = re.search(r"(\s+)last_end_dt = datetime\.fromisoformat\(last_end\.replace\('Z', '\+00:00'\)\)[\r\n]+\1days_diff = \(end_time - last_end_dt\)\.days", content)
        
        if match:
            indentation = match.group(1)  # Capture the indentation
            old_code = match.group(0)
            
            # Format the new code with the correct indentation
            new_code_lines = new_code.split('\n')
            new_code_formatted = f"\n{indentation}".join(new_code_lines)
            
            content = content.replace(old_code, new_code_formatted)
            print("Successfully found and replaced the code with regex matching.")
        else:
            print("Could not find the code to replace. Manual intervention may be required.")
            return
    
    # Write the updated content back to the file
    with open(chronos_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Updated {chronos_path} successfully!")
    print("The datetime handling issue in the get_candles method should now be fixed.")
    print("Please run the test script again to verify the fix.")

if __name__ == "__main__":
    fix_chronos_file() 