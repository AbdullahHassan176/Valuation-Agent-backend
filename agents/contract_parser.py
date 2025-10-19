"""
Contract parsing agent using spaCy and regex for PDF field extraction.
No external API calls - all processing is local.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import json


@dataclass
class ExtractedField:
    """Represents an extracted field with confidence score."""
    field_name: str
    value: Any
    confidence: float
    source_text: str
    start_pos: int
    end_pos: int


@dataclass
class ContractExtraction:
    """Complete contract extraction result."""
    fields: List[ExtractedField]
    instrument_type: str  # "IRS" or "CCS"
    overall_confidence: float
    raw_text: str


class ContractParser:
    """Main contract parser using spaCy NLP and regex patterns."""
    
    def __init__(self):
        # Simple text processing without spaCy
        pass
        
        # Define regex patterns for financial terms
        self.patterns = {
            "notional": [
                r"notional\s+(?:amount\s+)?(?:of\s+)?(?:usd\s+)?\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:million|m|billion|b)?",
                r"principal\s+(?:amount\s+)?(?:of\s+)?(?:usd\s+)?\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:million|m|billion|b)?",
                r"amount\s+(?:of\s+)?(?:usd\s+)?\$?([0-9,]+(?:\.[0-9]+)?)\s*(?:million|m|billion|b)?"
            ],
            "currency": [
                r"(?:currency|ccy|denominated\s+in)\s*:?\s*([A-Z]{3})",
                r"([A-Z]{3})\s+(?:currency|ccy)",
                r"usd|eur|gbp|jpy|chf|cad|aud"
            ],
            "fixed_rate": [
                r"fixed\s+rate\s*:?\s*([0-9]+(?:\.[0-9]+)?)\s*%",
                r"coupon\s+rate\s*:?\s*([0-9]+(?:\.[0-9]+)?)\s*%",
                r"rate\s*:?\s*([0-9]+(?:\.[0-9]+)?)\s*%"
            ],
            "floating_index": [
                r"(?:floating\s+)?(?:rate\s+)?(?:index\s+)?(?:based\s+on\s+)?(sofr|libor|euribor|fed\s+funds)",
                r"(sofr|libor|euribor|fed\s+funds)\s+(?:rate|index)",
                r"reference\s+rate\s*:?\s*(sofr|libor|euribor|fed\s+funds)"
            ],
            "effective_date": [
                r"effective\s+date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})",
                r"start\s+date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})",
                r"trade\s+date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})"
            ],
            "maturity_date": [
                r"maturity\s+date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})",
                r"end\s+date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})",
                r"termination\s+date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})"
            ],
            "frequency": [
                r"payment\s+frequency\s*:?\s*(quarterly|semi-annual|annual|monthly)",
                r"frequency\s*:?\s*(quarterly|semi-annual|annual|monthly)",
                r"(quarterly|semi-annual|annual|monthly)\s+payments?"
            ],
            "day_count": [
                r"day\s+count\s*:?\s*(act/360|act/365|30/360|30e/360)",
                r"day\s+count\s+convention\s*:?\s*(act/360|act/365|30/360|30e/360)",
                r"(act/360|act/365|30/360|30e/360)\s+day\s+count"
            ],
            "business_day_convention": [
                r"business\s+day\s+convention\s*:?\s*(following|preceding|modified\s+following)",
                r"bdc\s*:?\s*(following|preceding|modified\s+following)",
                r"(following|preceding|modified\s+following)\s+business\s+day"
            ]
        }
        
        # Confidence thresholds
        self.confidence_thresholds = {
            "notional": 0.7,
            "currency": 0.8,
            "fixed_rate": 0.6,
            "floating_index": 0.7,
            "effective_date": 0.8,
            "maturity_date": 0.8,
            "frequency": 0.6,
            "day_count": 0.5,
            "business_day_convention": 0.5
        }
    
    def parse_contract(self, text: str) -> ContractExtraction:
        """
        Parse contract text and extract financial instrument fields.
        
        Args:
            text: Raw text extracted from PDF
            
        Returns:
            ContractExtraction with fields and confidence scores
        """
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Extract fields using regex patterns
        extracted_fields = []
        
        for field_name, patterns in self.patterns.items():
            field_result = self._extract_field(cleaned_text, field_name, patterns)
            if field_result:
                extracted_fields.append(field_result)
        
        # Determine instrument type
        instrument_type = self._determine_instrument_type(cleaned_text)
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(extracted_fields)
        
        return ContractExtraction(
            fields=extracted_fields,
            instrument_type=instrument_type,
            overall_confidence=overall_confidence,
            raw_text=cleaned_text
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for better pattern matching."""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = text.lower()
        
        # Remove common PDF artifacts
        text = re.sub(r'[^\w\s%$.,/-]', ' ', text)
        
        return text.strip()
    
    def _extract_field(self, text: str, field_name: str, patterns: List[str]) -> Optional[ExtractedField]:
        """Extract a specific field using regex patterns."""
        best_match = None
        best_confidence = 0.0
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                confidence = self._calculate_pattern_confidence(match, field_name)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = match
        
        if best_match and best_confidence > 0.3:  # Minimum confidence threshold
            value = self._normalize_field_value(field_name, best_match.group(1))
            return ExtractedField(
                field_name=field_name,
                value=value,
                confidence=best_confidence,
                source_text=best_match.group(0),
                start_pos=best_match.start(),
                end_pos=best_match.end()
            )
        
        return None
    
    def _calculate_pattern_confidence(self, match: re.Match, field_name: str) -> float:
        """Calculate confidence score for a regex match."""
        base_confidence = 0.5
        
        # Boost confidence for exact matches
        if match.group(0).lower() in match.group(0).lower():
            base_confidence += 0.2
        
        # Boost confidence for longer matches (more context)
        match_length = len(match.group(0))
        if match_length > 20:
            base_confidence += 0.1
        elif match_length > 10:
            base_confidence += 0.05
        
        # Field-specific confidence adjustments
        if field_name == "notional":
            # Check if it looks like a reasonable notional amount
            try:
                amount = float(match.group(1).replace(',', ''))
                if 100000 <= amount <= 10000000000:  # $100K to $10B
                    base_confidence += 0.2
            except ValueError:
                pass
        
        elif field_name == "currency":
            # Currency codes are usually high confidence
            if len(match.group(1)) == 3 and match.group(1).isupper():
                base_confidence += 0.3
        
        elif field_name in ["effective_date", "maturity_date"]:
            # Date fields need validation
            try:
                date_str = match.group(1)
                # Try to parse the date
                datetime.strptime(date_str, "%m/%d/%Y")
                base_confidence += 0.2
            except ValueError:
                try:
                    datetime.strptime(date_str, "%m-%d-%Y")
                    base_confidence += 0.2
                except ValueError:
                    pass
        
        return min(base_confidence, 1.0)
    
    def _normalize_field_value(self, field_name: str, raw_value: str) -> Any:
        """Normalize extracted field values to proper types."""
        if field_name == "notional":
            # Convert to float, handle millions/billions
            value = raw_value.replace(',', '')
            if 'million' in raw_value.lower() or 'm' in raw_value.lower():
                return float(value) * 1000000
            elif 'billion' in raw_value.lower() or 'b' in raw_value.lower():
                return float(value) * 1000000000
            else:
                return float(value)
        
        elif field_name == "fixed_rate":
            return float(raw_value)
        
        elif field_name in ["effective_date", "maturity_date"]:
            # Parse date string
            try:
                return datetime.strptime(raw_value, "%m/%d/%Y").date()
            except ValueError:
                try:
                    return datetime.strptime(raw_value, "%m-%d-%Y").date()
                except ValueError:
                    return raw_value  # Return as string if can't parse
        
        elif field_name == "frequency":
            # Normalize frequency strings
            freq_map = {
                "quarterly": "3M",
                "semi-annual": "6M", 
                "annual": "1Y",
                "monthly": "1M"
            }
            return freq_map.get(raw_value.lower(), raw_value)
        
        elif field_name == "day_count":
            # Normalize day count conventions
            dc_map = {
                "act/360": "ACT/360",
                "act/365": "ACT/365F",
                "30/360": "30/360",
                "30e/360": "30E/360"
            }
            return dc_map.get(raw_value.lower(), raw_value.upper())
        
        elif field_name == "business_day_convention":
            # Normalize BDC
            bdc_map = {
                "following": "FOLLOWING",
                "preceding": "PRECEDING", 
                "modified following": "MODIFIED_FOLLOWING"
            }
            return bdc_map.get(raw_value.lower(), raw_value.upper())
        
        else:
            return raw_value.strip()
    
    def _determine_instrument_type(self, text: str) -> str:
        """Determine if this is an IRS or CCS based on text content."""
        ccs_indicators = [
            "cross currency", "currency swap", "ccs", "different currency",
            "eur/usd", "usd/eur", "gbp/usd", "usd/jpy"
        ]
        
        for indicator in ccs_indicators:
            if indicator in text:
                return "CCS"
        
        return "IRS"  # Default to IRS
    
    def _calculate_overall_confidence(self, fields: List[ExtractedField]) -> float:
        """Calculate overall confidence for the extraction."""
        if not fields:
            return 0.0
        
        # Weight by field importance
        weights = {
            "notional": 0.2,
            "currency": 0.15,
            "effective_date": 0.15,
            "maturity_date": 0.15,
            "fixed_rate": 0.1,
            "floating_index": 0.1,
            "frequency": 0.05,
            "day_count": 0.05,
            "business_day_convention": 0.05
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for field in fields:
            weight = weights.get(field.field_name, 0.05)
            weighted_sum += field.confidence * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def validate_extraction(self, extraction: ContractExtraction) -> Tuple[bool, List[str]]:
        """
        Validate extraction against confidence thresholds.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check required fields for IRS
        if extraction.instrument_type == "IRS":
            required_fields = ["notional", "currency", "effective_date", "maturity_date"]
        else:  # CCS
            required_fields = ["notional", "currency", "effective_date", "maturity_date"]
        
        field_dict = {f.field_name: f for f in extraction.fields}
        
        for required_field in required_fields:
            if required_field not in field_dict:
                issues.append(f"Missing required field: {required_field}")
            else:
                field = field_dict[required_field]
                threshold = self.confidence_thresholds.get(required_field, 0.5)
                if field.confidence < threshold:
                    issues.append(f"Low confidence ({field.confidence:.2f}) for required field: {required_field}")
        
        # Check overall confidence
        if extraction.overall_confidence < 0.6:
            issues.append(f"Overall confidence too low: {extraction.overall_confidence:.2f}")
        
        return len(issues) == 0, issues


def parse_contract_node(text: str) -> Dict[str, Any]:
    """
    LangGraph node function for contract parsing.
    
    Args:
        text: Raw text from PDF
        
    Returns:
        Dictionary with extraction results
    """
    parser = ContractParser()
    extraction = parser.parse_contract(text)
    is_valid, issues = parser.validate_extraction(extraction)
    
    # Convert to serializable format
    fields_data = []
    for field in extraction.fields:
        fields_data.append({
            "field_name": field.field_name,
            "value": field.value,
            "confidence": field.confidence,
            "source_text": field.source_text,
            "start_pos": field.start_pos,
            "end_pos": field.end_pos
        })
    
    return {
        "fields": fields_data,
        "instrument_type": extraction.instrument_type,
        "overall_confidence": extraction.overall_confidence,
        "is_valid": is_valid,
        "issues": issues,
        "raw_text": extraction.raw_text
    }
