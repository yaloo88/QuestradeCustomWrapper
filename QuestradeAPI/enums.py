"""
Questrade API Enumerations

This module provides Python enumerations for the various enum types used in the Questrade API.
These are based on the official API documentation and can be used for type checking and
reference in client applications.
"""

from enum import Enum, auto


class Currency(str, Enum):
    """Supported currency codes."""
    USD = "USD"  # US dollar
    CAD = "CAD"  # Canadian dollar


class ListingExchange(str, Enum):
    """Supported listing exchanges."""
    TSX = "TSX"               # Toronto Stock Exchange
    TSXV = "TSXV"             # Toronto Venture Exchange
    CNSX = "CNSX"             # Canadian National Stock Exchange
    MX = "MX"                 # Montreal Exchange
    NASDAQ = "NASDAQ"         # NASDAQ
    NYSE = "NYSE"             # New York Stock Exchange
    NYSEAM = "NYSEAM"         # NYSE AMERICAN
    ARCA = "ARCA"             # NYSE Arca
    OPRA = "OPRA"             # Option Reporting Authority
    PinkSheets = "PinkSheets" # Pink Sheets
    OTCBB = "OTCBB"           # OTC Bulletin Board


class AccountType(str, Enum):
    """Supported user account types."""
    Cash = "Cash"       # Cash account
    Margin = "Margin"   # Margin account
    TFSA = "TFSA"       # Tax Free Savings Account
    RRSP = "RRSP"       # Registered Retirement Savings Plan
    FHSA = "FHSA"       # First Home Savings Account
    SRRSP = "SRRSP"     # Spousal RRSP
    LRRSP = "LRRSP"     # Locked-In RRSP
    LIRA = "LIRA"       # Locked-In Retirement Account
    LIF = "LIF"         # Life Income Fund
    RIF = "RIF"         # Retirement Income Fund
    SRIF = "SRIF"       # Spousal RIF
    LRIF = "LRIF"       # Locked-In RIF
    RRIF = "RRIF"       # Registered RIF
    PRIF = "PRIF"       # Prescribed RIF
    RESP = "RESP"       # Individual Registered Education Savings Plan
    FRESP = "FRESP"     # Family RESP


class ClientAccountType(str, Enum):
    """Supported account client types."""
    Individual = "Individual"                   # Account held by an individual
    Joint = "Joint"                             # Account held jointly by several individuals
    InformalTrust = "Informal Trust"            # Non-individual account held by an informal trust
    Corporation = "Corporation"                 # Non-individual account held by a corporation
    FormalTrust = "Formal Trust"                # Non-individual account held by a formal trust
    Partnership = "Partnership"                 # Non-individual account held by a partnership
    SoleProprietorship = "Sole Proprietorship"  # Non-individual account held by a sole proprietorship
    Family = "Family"                           # Account held by a family
    JointAndInformalTrust = "Joint and Informal Trust"  # Non-individual account held by a joint and informal trust
    Institution = "Institution"                 # Non-individual account held by an institution


class AccountStatus(str, Enum):
    """Supported account status values."""
    Active = "Active"
    SuspendedClosed = "Suspended (Closed)"
    SuspendedViewOnly = "Suspended (View Only)"
    LiquidateOnly = "Liquidate Only"
    Closed = "Closed"


class TickType(str, Enum):
    """Supported market data tick types."""
    Up = "Up"        # Designates an uptick
    Down = "Down"    # Designates a downtick
    Equal = "Equal"  # Designates a tick that took place at the same price as a previous one


class OptionType(str, Enum):
    """Supported option types."""
    Call = "Call"  # Call option
    Put = "Put"    # Put option


class OptionDurationType(str, Enum):
    """Supported option duration types."""
    Weekly = "Weekly"      # Weekly expiry cycle
    Monthly = "Monthly"    # Monthly expiry cycle
    Quarterly = "Quarterly"  # Quarterly expiry cycle
    LEAP = "LEAP"          # Long-term Equity Appreciation contracts


class OptionExerciseType(str, Enum):
    """Supported option exercise types."""
    American = "American"  # American option
    European = "European"  # European option


class SecurityType(str, Enum):
    """Supported security types."""
    Stock = "Stock"              # Common and preferred equities, ETFs, ETNs, units, ADRs, etc.
    Option = "Option"            # Equity and index options
    Bond = "Bond"                # Debentures, notes, bonds, both corporate and government
    Right = "Right"              # Equity or bond rights and warrants
    Gold = "Gold"                # Physical gold (coins, wafers, bars)
    MutualFund = "MutualFund"    # Canadian or US mutual funds
    Index = "Index"              # Stock indices (e.g., Dow Jones)


class OrderStateFilterType(str, Enum):
    """Supported order state filter types."""
    All = "All"        # Includes all orders, regardless of their state
    Open = "Open"      # Includes only orders that are still open
    Closed = "Closed"  # Includes only orders that are already closed


class OrderAction(str, Enum):
    """Supported order side values."""
    Buy = "Buy"    # Designates an order to purchase a security
    Sell = "Sell"  # Designates an order to dispose a security


class OrderSide(str, Enum):
    """Supported client order side values."""
    Buy = "Buy"    # Buy
    Sell = "Sell"  # Sell
    Short = "Short"  # Sell short
    Cov = "Cov"    # Cover the short
    BTO = "BTO"    # Buy-To-Open
    STC = "STC"    # Sell-To-Close
    STO = "STO"    # Sell-To-Open
    BTC = "BTC"    # Buy-To-Close


class OrderType(str, Enum):
    """Supported order types."""
    Market = "Market"
    Limit = "Limit"
    Stop = "Stop"
    StopLimit = "StopLimit"
    TrailStopInPercentage = "TrailStopInPercentage"
    TrailStopInDollar = "TrailStopInDollar"
    TrailStopLimitInPercentage = "TrailStopLimitInPercentage"
    TrailStopLimitInDollar = "TrailStopLimitInDollar"
    LimitOnOpen = "LimitOnOpen"
    LimitOnClose = "LimitOnClose"


class OrderTimeInForce(str, Enum):
    """Supported order Time-In-Force instructions."""
    Day = "Day"
    GoodTillCanceled = "GoodTillCanceled"
    GoodTillExtendedDay = "GoodTillExtendedDay"
    GoodTillDate = "GoodTillDate"
    ImmediateOrCancel = "ImmediateOrCancel"
    FillOrKill = "FillOrKill"


class OrderState(str, Enum):
    """Supported order states."""
    Failed = "Failed"
    Pending = "Pending"
    Accepted = "Accepted"
    Rejected = "Rejected"
    CancelPending = "CancelPending"
    Canceled = "Canceled"
    PartialCanceled = "PartialCanceled"
    Partial = "Partial"
    Executed = "Executed"
    ReplacePending = "ReplacePending"
    Replaced = "Replaced"
    Stopped = "Stopped"
    Suspended = "Suspended"
    Expired = "Expired"
    Queued = "Queued"
    Triggered = "Triggered"
    Activated = "Activated"
    PendingRiskReview = "PendingRiskReview"
    ContingentOrder = "ContingentOrder"


class HistoricalDataGranularity(str, Enum):
    """Supported historical data granularity values."""
    OneMinute = "OneMinute"              # One candlestick per 1 minute
    TwoMinutes = "TwoMinutes"            # One candlestick per 2 minutes
    ThreeMinutes = "ThreeMinutes"        # One candlestick per 3 minutes
    FourMinutes = "FourMinutes"          # One candlestick per 4 minutes
    FiveMinutes = "FiveMinutes"          # One candlestick per 5 minutes
    TenMinutes = "TenMinutes"            # One candlestick per 10 minutes
    FifteenMinutes = "FifteenMinutes"    # One candlestick per 15 minutes
    TwentyMinutes = "TwentyMinutes"      # One candlestick per 20 minutes
    HalfHour = "HalfHour"                # One candlestick per 30 minutes
    OneHour = "OneHour"                  # One candlestick per 1 hour
    TwoHours = "TwoHours"                # One candlestick per 2 hours
    FourHours = "FourHours"              # One candlestick per 4 hours
    OneDay = "OneDay"                    # One candlestick per 1 day
    OneWeek = "OneWeek"                  # One candlestick per 1 week
    OneMonth = "OneMonth"                # One candlestick per 1 month
    OneYear = "OneYear"                  # One candlestick per 1 year


class OrderClass(str, Enum):
    """Supported bracket order components."""
    Primary = "Primary"      # Primary order
    Limit = "Limit"          # Profit exit order
    StopLoss = "StopLoss"    # Loss exit order


class StrategyType(str, Enum):
    """Supported strategy types for multi-leg strategy orders."""
    CoveredCall = "CoveredCall"                # Covered Call
    MarriedPuts = "MarriedPuts"                # Married Put
    VerticalCallSpread = "VerticalCallSpread"  # Vertical Call
    VerticalPutSpread = "VerticalPutSpread"    # Vertical Put
    CalendarCallSpread = "CalendarCallSpread"  # Calendar Call
    CalendarPutSpread = "CalendarPutSpread"    # Calendar Put
    DiagonalCallSpread = "DiagonalCallSpread"  # Diagonal Call
    DiagonalPutSpread = "DiagonalPutSpread"    # Diagonal Put
    Collar = "Collar"                          # Collar
    Straddle = "Straddle"                      # Straddle
    Strangle = "Strangle"                      # Strangle
    ButterflyCall = "ButterflyCall"            # Butterfly Call
    ButterflyPut = "ButterflyPut"              # Butterfly Put
    IronButterfly = "IronButterfly"            # Iron Butterfly
    CondorCall = "CondorCall"                  # Condor
    Custom = "Custom"                          # Custom, or user defined 