# Backend models - simplified versions for proxy functionality
from typing import Union, List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel

class IRSSpec(BaseModel):
    """Interest Rate Swap specification"""
    type: str = "IRS"
    notional: float
    currency: str
    payFixed: bool
    fixedRate: Optional[float] = None
    floatIndex: str
    effective: Union[str, date]
    maturity: Union[str, date]
    dcFixed: str
    dcFloat: str
    freqFixed: str
    freqFloat: str
    calendar: str
    bdc: str
    csa: Optional[str] = None

class CCSSpec(BaseModel):
    """Cross Currency Swap specification"""
    type: str = "CCS"
    ccy1: str
    ccy2: str
    notional1: float
    notional2: float
    index1: str
    index2: str
    effective: Union[str, date]
    maturity: Union[str, date]
    freq1: str
    freq2: str
    calendar: str
    bdc: str
    reportingCcy: str

class RunRequest(BaseModel):
    """Request to run a valuation"""
    spec: Union[IRSSpec, CCSSpec]
    asOf: Union[str, date]
    marketDataProfile: str
    approach: List[str]

class RunStatus(BaseModel):
    """Status of a valuation run"""
    id: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    spec: Optional[Union[IRSSpec, CCSSpec]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class PVBreakdown(BaseModel):
    """Present Value breakdown with lineage information"""
    total_pv: float
    components: Dict[str, float]
    currency: str
    data_hash: Optional[str] = None
    model_hash: Optional[str] = None
    calculation_time: Optional[float] = None

