# Changelog

All notable changes to the Questrade API Wrapper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2023-03-21

### Added
- Rate limiting functionality with the `RateLimiter` class
  - Automatic tracking of request rates for both per-second and per-hour limits
  - Adaptive waiting when approaching rate limits
  - Header parsing for Questrade's rate limit headers
  - Configurable retries when rate limits are reached
  - Option to disable rate limiting for specialized use cases
- Structured error handling with custom exception classes
  - `QuestradeAPIError`: Base exception class
  - `QuestradeGeneralError`: For general API errors 
  - `QuestradeOrderError`: For order processing errors
  - `QuestradeRateLimitError`: For rate limit errors
- Type-safe enumerations for API parameters in `enums.py`
- Comprehensive documentation in `DOCUMENTATION.md`
- Example scripts demonstrating error handling and rate limiting
- Validation script for testing rate limiting functionality

### Changed
- Improved error handling in the `_make_request` method
- Updated README.md with information about rate limiting and error handling
- Enhanced QUICKSTART.md with examples of using the new features
- Refactored API validator to test rate limiting functionality
- Updated example scripts to demonstrate new features

### Fixed
- Improved error message formatting for better readability
- Fixed issues with nested error handling in API responses

## [1.0.0] - 2023-03-15

### Added
- Initial release of the Questrade API Wrapper
- Basic functionality for accessing Questrade API endpoints
- Support for authentication with refresh tokens
- Account endpoints (positions, balances, orders, activities)
- Market data endpoints (symbols, quotes, candles)
- Basic error handling
- Initial documentation in README.md 