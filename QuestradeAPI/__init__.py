"""
Questrade Custom API Wrapper

This package provides a custom wrapper for the Questrade API with additional
features like rate limiting, error handling, and convenience methods.
"""

from .CustomWrapper import (
    QuestradeAPI,
    QuestradeAPIError,
    QuestradeGeneralError,
    QuestradeOrderError,
    QuestradeRateLimitError
)

from .RateLimiter import RateLimiter, ApiCategory
from .enums import *

__all__ = [
    'QuestradeAPI',
    'QuestradeAPIError',
    'QuestradeGeneralError',
    'QuestradeOrderError',
    'QuestradeRateLimitError',
    'RateLimiter',
    'ApiCategory'
] 