@echo off
echo Running Chronos verification tests...
echo.
echo ===================================================
echo VERIFICATION TEST - Checking against example usage
echo ===================================================
python test_chronos_examples.py
echo.
echo.
echo ===================================================
echo COMPREHENSIVE TEST - Full functionality testing
echo ===================================================
python test_chronos.py
echo.
echo All tests completed.
pause 