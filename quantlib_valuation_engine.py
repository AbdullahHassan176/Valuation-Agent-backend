"""
QuantLib-based valuation engine for IRS and CCS instruments.
Provides comprehensive financial calculations with detailed reporting.
"""

# Try to import QuantLib, fallback to simplified calculations
try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False
    print("⚠️ QuantLib not available, using simplified calculations")

import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import math

class QuantLibValuationEngine:
    """Advanced valuation engine using QuantLib for IRS and CCS instruments."""
    
    def __init__(self):
        if QUANTLIB_AVAILABLE:
            self.calendar = ql.TARGET()
            self.day_count = ql.Actual360()
            self.compounding = ql.Compounded
            self.frequency = ql.Annual
        else:
            print("⚠️ QuantLib not available - using simplified calculations")
    
    def create_yield_curve(self, rates: List[float], tenors: List[float], 
                          curve_type: str = "zero"):
        """Create a yield curve from market rates."""
        if not QUANTLIB_AVAILABLE:
            # Return simplified curve data for fallback calculations
            return {
                "rates": rates,
                "tenors": tenors,
                "type": curve_type,
                "simplified": True
            }
        
        try:
            # Convert tenors to QuantLib periods
            periods = []
            for tenor in tenors:
                if tenor <= 1.0:
                    periods.append(ql.Period(int(tenor * 365), ql.Days))
                elif tenor <= 12.0:
                    periods.append(ql.Period(int(tenor), ql.Months))
                else:
                    periods.append(ql.Period(int(tenor / 12), ql.Years))
            
            # Create rate helpers
            rate_helpers = []
            for i, (rate, period) in enumerate(zip(rates, periods)):
                if curve_type == "zero":
                    # Use DepositRateHelper for short-term rates
                    if period.length() <= 12:  # Less than 1 year
                        rate_helpers.append(ql.DepositRateHelper(
                            ql.QuoteHandle(ql.SimpleQuote(rate)),
                            period,
                            self.calendar,
                            ql.ModifiedFollowing,
                            False, # End of month
                            self.day_count
                        ))
                    else:  # Longer term - use SwapRateHelper
                        rate_helpers.append(ql.SwapRateHelper(
                            ql.QuoteHandle(ql.SimpleQuote(rate)),
                            period,
                            self.calendar,
                            self.frequency,
                            self.day_count,
                            ql.Euribor6M() # Placeholder index
                        ))
                else:  # swap curve
                    rate_helpers.append(ql.SwapRateHelper(
                        ql.QuoteHandle(ql.SimpleQuote(rate)),
                        period,
                        self.calendar,
                        self.frequency,
                        self.day_count,
                        ql.Euribor6M() # Placeholder index
                    ))
            
            # Build the curve
            curve = ql.PiecewiseFlatForward(
                ql.Date.todaysDate(),
                rate_helpers,
                self.day_count
            )
            
            return ql.YieldTermStructureHandle(curve)
        except Exception as e:
            print(f"❌ Error creating yield curve: {e}")
            # Fallback to a flat curve if QuantLib curve creation fails
            return ql.YieldTermStructureHandle(
                ql.FlatForward(
                    ql.Date.todaysDate(),
                    ql.QuoteHandle(ql.SimpleQuote(0.02)),
                    self.day_count
                )
            )
    
    def value_interest_rate_swap(self, 
                                notional: float,
                                fixed_rate: float,
                                tenor_years: float,
                                frequency: str = "SemiAnnual",
                                curve_rates: List[float] = None,
                                curve_tenors: List[float] = None) -> Dict[str, Any]:
        """Value an Interest Rate Swap using QuantLib."""
        if not QUANTLIB_AVAILABLE:
            return self._simplified_irs_valuation(notional, fixed_rate, tenor_years, frequency, curve_rates, curve_tenors)
        
        try:
            # Set up evaluation date
            ql.Settings.instance().evaluationDate = ql.Date.todaysDate()
            
            # Create yield curve
            if curve_rates is None:
                curve_rates = [0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]
            if curve_tenors is None:
                curve_tenors = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 30.0]
            
            discount_curve = self.create_yield_curve(curve_rates, curve_tenors)
            
            # Define swap parameters
            settlement_date = self.calendar.advance(ql.Date.todaysDate(), ql.Period(2, ql.Days))
            maturity_date = self.calendar.advance(settlement_date, ql.Period(int(tenor_years), ql.Years))
            
            fixed_leg_tenor = ql.Period(ql.Semiannual) if frequency == "SemiAnnual" else ql.Period(ql.Annual)
            floating_leg_tenor = ql.Period(ql.Semiannual) if frequency == "SemiAnnual" else ql.Period(ql.Annual)
            
            # Create schedules
            fixed_schedule = ql.Schedule(settlement_date, maturity_date, fixed_leg_tenor,
                                        self.calendar, ql.ModifiedFollowing, ql.ModifiedFollowing,
                                        ql.DateGeneration.Forward, False)
            
            floating_schedule = ql.Schedule(settlement_date, maturity_date, floating_leg_tenor,
                                            self.calendar, ql.ModifiedFollowing, ql.ModifiedFollowing,
                                            ql.DateGeneration.Forward, False)
            
            # Create IborIndex (e.g., USD Libor 6M)
            index = ql.USDLibor(ql.Period(6, ql.Months), discount_curve)
            
            # Create the swap legs
            fixed_leg = ql.FixedRateLeg(fixed_schedule, self.day_count)
            fixed_leg.withNotionals(notional)
            fixed_leg.withCouponRates(fixed_rate)
            
            floating_leg = ql.IborLeg(floating_schedule, index)
            floating_leg.withNotionals(notional)
            floating_leg.withPaymentDayCounter(self.day_count)
            floating_leg.withFixingDays(2)
            
            # Create swap instrument
            swap = ql.Swap([fixed_leg, floating_leg])
            
            # Create pricing engine
            swap_engine = ql.DiscountingSwapEngine(discount_curve)
            swap.setPricingEngine(swap_engine)
            
            # Get NPV and fair rate
            npv = swap.NPV()
            fair_rate = swap.fairRate()
            
            # Calculate cash flows
            cash_flows = []
            for i, cf in enumerate(swap.leg(0)): # Fixed leg
                cash_flows.append({
                    "date": ql.Date.to_date(cf.date()).isoformat(),
                    "amount": cf.amount(),
                    "type": "Fixed",
                    "currency": "Base",
                    "leg": "Fixed"
                })
            for i, cf in enumerate(swap.leg(1)): # Floating leg
                cash_flows.append({
                    "date": ql.Date.to_date(cf.date()).isoformat(),
                    "amount": cf.amount(),
                    "type": "Floating",
                    "currency": "Base",
                    "leg": "Floating"
                })
            
            # Calculate risk metrics (simplified for now, can be expanded with AAD)
            risk_metrics = {
                "dv01": swap.NPV() * 0.0001, # Placeholder
                "duration": tenor_years * 0.8, # Placeholder
                "convexity": tenor_years * 0.1, # Placeholder
                "var_1d_99pct": abs(npv) * 0.05, # Placeholder
                "es_1d_99pct": abs(npv) * 0.07, # Placeholder
                "npv": npv,
                "notional": notional,
                "leverage": abs(npv / notional) if notional != 0 else 0
            }
            
            return {
                "instrument_type": "Interest Rate Swap",
                "notional": notional,
                "fixed_rate": fixed_rate,
                "fair_rate": fair_rate,
                "tenor_years": tenor_years,
                "frequency": frequency,
                "npv": npv,
                "annuity": swap.fixedLegBPS() / (fixed_rate * 10000), # Simplified annuity
                "cash_flows": cash_flows,
                "risk_metrics": risk_metrics,
                "methodology": {
                    "valuation_framework": "QuantLib Discounting Swap Engine",
                    "model": "Bootstrapped Yield Curve",
                    "assumptions": {
                        "discount_curve_type": "Zero Curve",
                        "day_count_convention": "Actual/360",
                        "business_day_convention": "ModifiedFollowing"
                    },
                    "formulae": {
                        "npv": "Sum(Discounted Cash Flows)",
                        "fair_rate": "Rate that makes NPV = 0"
                    }
                },
                "valuation_date": ql.Date.todaysDate().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error valuing IRS: {e}")
            return self._create_error_response("IRS", str(e))
    
    def value_cross_currency_swap(self,
                                 notional_base: float,
                                 notional_quote: float,
                                 base_currency: str,
                                 quote_currency: str,
                                 fixed_rate_base: float,
                                 fixed_rate_quote: float,
                                 tenor_years: float,
                                 frequency: str = "SemiAnnual",
                                 fx_rate: float = 1.0) -> Dict[str, Any]:
        """Value a Cross Currency Swap using QuantLib."""
        if not QUANTLIB_AVAILABLE:
            return self._simplified_ccs_valuation(notional_base, notional_quote, base_currency, 
                                                 quote_currency, fixed_rate_base, fixed_rate_quote, 
                                                 tenor_years, frequency, fx_rate)
        
        try:
            # Set up evaluation date
            ql.Settings.instance().evaluationDate = ql.Date.todaysDate()
            
            # Create yield curves for both currencies
            # Base currency curve (e.g., USD)
            base_curve_rates = [0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]
            base_curve_tenors = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 30.0]
            base_discount_curve = self.create_yield_curve(base_curve_rates, base_curve_tenors)
            
            # Quote currency curve (e.g., EUR)
            quote_curve_rates = [0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045]
            quote_curve_tenors = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 30.0]
            quote_discount_curve = self.create_yield_curve(quote_curve_rates, quote_curve_tenors)
            
            # Define swap parameters
            settlement_date = self.calendar.advance(ql.Date.todaysDate(), ql.Period(2, ql.Days))
            maturity_date = self.calendar.advance(settlement_date, ql.Period(int(tenor_years), ql.Years))
            
            fixed_leg_tenor = ql.Period(ql.Semiannual) if frequency == "SemiAnnual" else ql.Period(ql.Annual)
            
            # Create schedules
            schedule = ql.Schedule(settlement_date, maturity_date, fixed_leg_tenor,
                                        self.calendar, ql.ModifiedFollowing, ql.ModifiedFollowing,
                                        ql.DateGeneration.Forward, False)
            
            # Create IborIndex for both currencies (simplified)
            base_index = ql.USDLibor(ql.Period(6, ql.Months), base_discount_curve)
            quote_index = ql.Euribor(ql.Period(6, ql.Months), quote_discount_curve)
            
            # Create fixed legs for both currencies
            base_fixed_leg = ql.FixedRateLeg(schedule, self.day_count)
            base_fixed_leg.withNotionals(notional_base)
            base_fixed_leg.withCouponRates(fixed_rate_base)
            
            quote_fixed_leg = ql.FixedRateLeg(schedule, self.day_count)
            quote_fixed_leg.withNotionals(notional_quote)
            quote_fixed_leg.withCouponRates(fixed_rate_quote)
            
            # Create floating legs
            base_floating_leg = ql.IborLeg(schedule, base_index)
            base_floating_leg.withNotionals(notional_base)
            base_floating_leg.withPaymentDayCounter(self.day_count)
            base_floating_leg.withFixingDays(2)
            
            quote_floating_leg = ql.IborLeg(schedule, quote_index)
            quote_floating_leg.withNotionals(notional_quote)
            quote_floating_leg.withPaymentDayCounter(self.day_count)
            quote_floating_leg.withFixingDays(2)
            
            # Create Cross Currency Swap instrument
            # For simplicity, assuming a fixed-for-fixed CCS, or fixed-for-floating if floating rate is 0.0
            # QuantLib's CrossCurrencySwap is more complex, using VanillaSwap for illustration
            
            # Pricing engine for each currency
            base_engine = ql.DiscountingSwapEngine(base_discount_curve)
            quote_engine = ql.DiscountingSwapEngine(quote_discount_curve)
            
            # Calculate NPV for each leg
            base_fixed_npv = ql.CashFlows.npv(base_fixed_leg, base_discount_curve, False)
            base_floating_npv = ql.CashFlows.npv(base_floating_leg, base_discount_curve, False)
            
            quote_fixed_npv = ql.CashFlows.npv(quote_fixed_leg, quote_discount_curve, False)
            quote_floating_npv = ql.CashFlows.npv(quote_floating_leg, quote_discount_curve, False)
            
            # Total NPV in base currency
            npv_base = (base_fixed_npv - base_floating_npv) + (quote_fixed_npv - quote_floating_npv) * fx_rate
            npv_quote = npv_base / fx_rate
            
            # Cash flows (simplified for CCS)
            cash_flows = []
            for cf in base_fixed_leg:
                cash_flows.append({"date": ql.Date.to_date(cf.date()).isoformat(), "amount": cf.amount(), "type": "Fixed", "currency": base_currency, "leg": "Base Fixed"})
            for cf in base_floating_leg:
                cash_flows.append({"date": ql.Date.to_date(cf.date()).isoformat(), "amount": cf.amount(), "type": "Floating", "currency": base_currency, "leg": "Base Floating"})
            for cf in quote_fixed_leg:
                cash_flows.append({"date": ql.Date.to_date(cf.date()).isoformat(), "amount": cf.amount(), "type": "Fixed", "currency": quote_currency, "leg": "Quote Fixed"})
            for cf in quote_floating_leg:
                cash_flows.append({"date": ql.Date.to_date(cf.date()).isoformat(), "amount": cf.amount(), "type": "Floating", "currency": quote_currency, "leg": "Quote Floating"})
            
            # Risk metrics (simplified for now)
            risk_metrics = {
                "dv01": npv_base * 0.0001, # Placeholder
                "duration": tenor_years * 0.8, # Placeholder
                "convexity": tenor_years * 0.1, # Placeholder
                "var_1d_99pct": abs(npv_base) * 0.05, # Placeholder
                "es_1d_99pct": abs(npv_base) * 0.07, # Placeholder
                "npv": npv_base,
                "notional": notional_base,
                "leverage": abs(npv_base / notional_base) if notional_base != 0 else 0
            }
            
            return {
                "instrument_type": "Cross Currency Swap",
                "notional_base": notional_base,
                "notional_quote": notional_quote,
                "base_currency": base_currency,
                "quote_currency": quote_currency,
                "fixed_rate_base": fixed_rate_base,
                "fixed_rate_quote": fixed_rate_quote,
                "tenor_years": tenor_years,
                "frequency": frequency,
                "fx_rate": fx_rate,
                "npv_base": npv_base,
                "npv_quote": npv_quote,
                "cash_flows": cash_flows,
                "risk_metrics": risk_metrics,
                "methodology": {
                    "valuation_framework": "QuantLib Discounting Legs",
                    "model": "Bootstrapped Yield Curves",
                    "assumptions": {
                        "base_discount_curve_type": "Zero Curve",
                        "quote_discount_curve_type": "Zero Curve",
                        "day_count_convention": "Actual/360",
                        "business_day_convention": "ModifiedFollowing",
                        "fx_rate_source": "Spot"
                    },
                    "formulae": {
                        "npv_base": "NPV(Base Leg) + NPV(Quote Leg) * FX Rate"
                    }
                },
                "valuation_date": ql.Date.todaysDate().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error valuing CCS: {e}")
            return self._create_error_response("CCS", str(e))
    
    def _create_error_response(self, instrument_type: str, error_message: str) -> Dict[str, Any]:
        """Helper to create a standardized error response."""
        return {
            "instrument_type": instrument_type,
            "npv": 0.0,
            "npv_base": 0.0,
            "npv_quote": 0.0,
            "risk_metrics": {},
            "cash_flows": [],
            "methodology": {
                "valuation_framework": "Error",
                "model": "N/A",
                "assumptions": {"error": error_message},
                "formulae": {"error": error_message}
            },
            "error": error_message,
            "valuation_date": datetime.now().isoformat()
        }
    
    def _simplified_irs_valuation(self, notional: float, fixed_rate: float, 
                                  tenor_years: float, frequency: str,
                                  curve_rates: List[float], curve_tenors: List[float]) -> Dict[str, Any]:
        """Simplified IRS valuation when QuantLib is not available."""
        # Simple NPV calculation based on interest rate differential
        market_rate = 0.04  # Assume 4% market rate
        rate_diff = fixed_rate - market_rate
        duration = tenor_years * 0.8
        npv = rate_diff * notional * duration
        
        # Ensure NPV is reasonable
        max_npv = notional * 0.1
        if abs(npv) > max_npv:
            npv = max_npv if npv > 0 else -max_npv
        
        return {
            "instrument_type": "Interest Rate Swap",
            "notional": notional,
            "fixed_rate": fixed_rate,
            "fair_rate": market_rate,
            "tenor_years": tenor_years,
            "frequency": frequency,
            "npv": npv,
            "annuity": tenor_years * 0.8,
            "cash_flows": self._simplified_cash_flows(notional, fixed_rate, tenor_years, frequency),
            "risk_metrics": {
                "dv01": abs(notional * duration * 0.0001),
                "duration": duration,
                "convexity": tenor_years * 0.1,
                "var_1d_99pct": abs(npv) * 0.05,
                "es_1d_99pct": abs(npv) * 0.07,
                "npv": npv,
                "notional": notional,
                "leverage": abs(npv / notional) if notional != 0 else 0
            },
            "methodology": self._simplified_methodology("IRS"),
            "valuation_date": datetime.now().isoformat()
        }
    
    def _simplified_ccs_valuation(self, notional_base: float, notional_quote: float,
                                  base_currency: str, quote_currency: str,
                                  fixed_rate_base: float, fixed_rate_quote: float,
                                  tenor_years: float, frequency: str, fx_rate: float) -> Dict[str, Any]:
        """Simplified CCS valuation when QuantLib is not available."""
        # Simple NPV calculation for each currency
        market_rate_base = 0.04
        market_rate_quote = 0.03
        
        rate_diff_base = fixed_rate_base - market_rate_base
        rate_diff_quote = fixed_rate_quote - market_rate_quote
        
        duration = tenor_years * 0.8
        
        npv_base = rate_diff_base * notional_base * duration
        npv_quote = rate_diff_quote * notional_quote * duration
        
        # Total NPV in base currency
        npv_total = npv_base + npv_quote * fx_rate
        
        return {
            "instrument_type": "Cross Currency Swap",
            "notional_base": notional_base,
            "notional_quote": notional_quote,
            "base_currency": base_currency,
            "quote_currency": quote_currency,
            "fixed_rate_base": fixed_rate_base,
            "fixed_rate_quote": fixed_rate_quote,
            "tenor_years": tenor_years,
            "frequency": frequency,
            "fx_rate": fx_rate,
            "npv_base": npv_total,
            "npv_quote": npv_total / fx_rate,
            "cash_flows": self._simplified_cash_flows(notional_base, fixed_rate_base, tenor_years, frequency),
            "risk_metrics": {
                "dv01": abs(notional_base * duration * 0.0001),
                "duration": duration,
                "convexity": tenor_years * 0.1,
                "var_1d_99pct": abs(npv_total) * 0.05,
                "es_1d_99pct": abs(npv_total) * 0.07,
                "npv": npv_total,
                "notional": notional_base,
                "leverage": abs(npv_total / notional_base) if notional_base != 0 else 0
            },
            "methodology": self._simplified_methodology("CCS"),
            "valuation_date": datetime.now().isoformat()
        }
    
    def _simplified_cash_flows(self, notional: float, rate: float, 
                              tenor_years: float, frequency: str) -> List[Dict[str, Any]]:
        """Generate simplified cash flows."""
        cash_flows = []
        periods_per_year = 2 if frequency == "SemiAnnual" else 1
        total_periods = int(tenor_years * periods_per_year)
        
        for i in range(total_periods):
            date_offset = (i + 1) / periods_per_year
            payment_date = datetime.now() + timedelta(days=365 * date_offset)
            amount = notional * rate / periods_per_year
            
            cash_flows.append({
                "date": payment_date.isoformat(),
                "amount": amount,
                "type": "Fixed",
                "currency": "Base",
                "leg": "Fixed"
            })
        
        return cash_flows
    
    def _simplified_methodology(self, instrument_type: str) -> Dict[str, Any]:
        """Generate simplified methodology documentation."""
        return {
            "valuation_framework": "Simplified Interest Rate Differential",
            "model": "Market Rate vs Fixed Rate",
            "assumptions": {
                "market_rate": "Assumed market rate",
                "day_count_convention": "Simplified",
                "business_day_convention": "Simplified"
            },
            "formulae": {
                "npv": "Rate Differential × Notional × Duration",
                "duration": "Tenor × 0.8"
            }
        }
