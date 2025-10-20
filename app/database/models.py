"""
Database models for the Valuation Agent.
Defines all data structures for runs, valuations, curves, and market data.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class RunStatus(str, Enum):
    """Status of a valuation run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ValuationType(str, Enum):
    """Type of valuation."""
    IRS = "irs"
    CCS = "ccs"
    BOND = "bond"
    SWAPTION = "swaption"
    CAP_FLOOR = "cap_floor"

class CurveType(str, Enum):
    """Type of interest rate curve."""
    OIS = "ois"
    SOFR = "sofr"
    EURIBOR = "euribor"
    SONIA = "sonia"
    ESTR = "estr"

class Currency(str, Enum):
    """Supported currencies."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CHF = "CHF"
    CAD = "CAD"
    AUD = "AUD"

# Base Models
class BaseRecord(BaseModel):
    """Base record with common fields."""
    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User who created the record")

# Market Data Models
class MarketDataPoint(BaseModel):
    """Individual market data point."""
    tenor: str = Field(..., description="Tenor (e.g., '1M', '3M', '1Y')")
    rate: float = Field(..., description="Interest rate")
    date: datetime = Field(..., description="Market data date")
    source: str = Field(..., description="Data source (e.g., 'Bloomberg', 'Reuters')")

class Curve(BaseRecord):
    """Interest rate curve."""
    name: str = Field(..., description="Curve name")
    currency: Currency = Field(..., description="Currency")
    curve_type: CurveType = Field(..., description="Type of curve")
    as_of_date: datetime = Field(..., description="As of date")
    nodes: List[MarketDataPoint] = Field(default_factory=list)
    status: str = Field(default="active", description="Curve status")
    version: str = Field(default="1.0.0", description="Curve version")

# Valuation Models
class IRSSpec(BaseModel):
    """Interest Rate Swap specification."""
    notional: float = Field(..., description="Notional amount")
    currency: Currency = Field(..., description="Currency")
    pay_fixed: bool = Field(..., description="True if paying fixed rate")
    fixed_rate: Optional[float] = Field(None, description="Fixed rate (if applicable)")
    float_index: str = Field(..., description="Floating rate index")
    effective_date: datetime = Field(..., description="Effective date")
    maturity_date: datetime = Field(..., description="Maturity date")
    day_count_fixed: str = Field(default="ACT/360", description="Day count convention for fixed leg")
    day_count_float: str = Field(default="ACT/360", description="Day count convention for floating leg")
    frequency_fixed: str = Field(default="Semi-Annual", description="Fixed leg frequency")
    frequency_float: str = Field(default="Quarterly", description="Floating leg frequency")
    calendar: str = Field(default="TARGET", description="Business day calendar")
    business_day_convention: str = Field(default="Modified Following", description="Business day convention")

class CCSSpec(BaseModel):
    """Cross Currency Swap specification."""
    notional_leg1: float = Field(..., description="Notional for leg 1")
    notional_leg2: float = Field(..., description="Notional for leg 2")
    currency_leg1: Currency = Field(..., description="Currency for leg 1")
    currency_leg2: Currency = Field(..., description="Currency for leg 2")
    index_leg1: str = Field(..., description="Index for leg 1")
    index_leg2: str = Field(..., description="Index for leg 2")
    effective_date: datetime = Field(..., description="Effective date")
    maturity_date: datetime = Field(..., description="Maturity date")
    day_count: str = Field(default="ACT/360", description="Day count convention")
    frequency: str = Field(default="Quarterly", description="Payment frequency")
    calendar: str = Field(default="TARGET", description="Business day calendar")
    business_day_convention: str = Field(default="Modified Following", description="Business day convention")
    constant_notional: bool = Field(default=True, description="Whether notional is constant")

class PVBreakdown(BaseModel):
    """Present Value breakdown."""
    pv_base_currency: float = Field(..., description="PV in base currency")
    pv_reporting_currency: Optional[float] = Field(None, description="PV in reporting currency")
    legs: List[Dict[str, Any]] = Field(default_factory=list, description="PV breakdown by leg")
    sensitivities: List[Dict[str, Any]] = Field(default_factory=list, description="Risk sensitivities")

class ValuationRun(BaseRecord):
    """Valuation run record."""
    run_id: str = Field(..., description="Unique run identifier")
    as_of_date: datetime = Field(..., description="As of date for valuation")
    valuation_type: ValuationType = Field(..., description="Type of valuation")
    spec: Dict[str, Any] = Field(..., description="Valuation specification")
    market_data_profile: str = Field(default="synthetic", description="Market data profile used")
    status: RunStatus = Field(default=RunStatus.PENDING, description="Run status")
    result: Optional[PVBreakdown] = Field(None, description="Valuation result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    curve_ids: List[str] = Field(default_factory=list, description="Curve IDs used")
    execution_time_ms: Optional[int] = Field(None, description="Execution time in milliseconds")

# User and Session Models
class User(BaseRecord):
    """User account."""
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: str = Field(..., description="Full name")
    is_active: bool = Field(default=True, description="Whether user is active")
    last_login: Optional[datetime] = Field(None, description="Last login time")

class Session(BaseRecord):
    """User session."""
    user_id: str = Field(..., description="User ID")
    session_token: str = Field(..., description="Session token")
    expires_at: datetime = Field(..., description="Session expiration")
    is_active: bool = Field(default=True, description="Whether session is active")

# Audit and Logging Models
class AuditLog(BaseRecord):
    """Audit log entry."""
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Type of resource")
    resource_id: str = Field(..., description="Resource ID")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Old values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")

class SystemLog(BaseRecord):
    """System log entry."""
    level: str = Field(..., description="Log level (DEBUG, INFO, WARNING, ERROR)")
    message: str = Field(..., description="Log message")
    module: str = Field(..., description="Module name")
    function: str = Field(..., description="Function name")
    line_number: int = Field(..., description="Line number")
    exception: Optional[str] = Field(None, description="Exception details")

# Configuration Models
class SystemConfig(BaseRecord):
    """System configuration."""
    key: str = Field(..., description="Configuration key")
    value: str = Field(..., description="Configuration value")
    description: Optional[str] = Field(None, description="Configuration description")
    is_encrypted: bool = Field(default=False, description="Whether value is encrypted")

class MarketDataConfig(BaseRecord):
    """Market data configuration."""
    source_name: str = Field(..., description="Data source name")
    source_type: str = Field(..., description="Source type (API, FILE, MANUAL)")
    connection_string: Optional[str] = Field(None, description="Connection string")
    credentials: Optional[Dict[str, str]] = Field(None, description="Credentials")
    is_active: bool = Field(default=True, description="Whether source is active")
    refresh_interval_minutes: int = Field(default=60, description="Refresh interval in minutes")



