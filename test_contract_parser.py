#!/usr/bin/env python3
"""
Test script for the contract parser functionality.
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from agents.contract_parser import ContractParser, parse_contract_node

def test_contract_parser():
    """Test the contract parser with sample text."""
    
    # Sample contract text
    sample_text = """
    INTEREST RATE SWAP AGREEMENT
    
    This Interest Rate Swap Agreement is entered into on January 15, 2024.
    
    TERMS AND CONDITIONS:
    
    1. NOTIONAL AMOUNT: USD 10,000,000 (Ten Million US Dollars)
    2. CURRENCY: USD (United States Dollar)
    3. FIXED RATE: 5.25% per annum
    4. FLOATING RATE INDEX: SOFR (Secured Overnight Financing Rate)
    5. EFFECTIVE DATE: March 1, 2024
    6. MATURITY DATE: March 1, 2025
    7. PAYMENT FREQUENCY: Quarterly
    8. DAY COUNT CONVENTION: ACT/360
    9. BUSINESS DAY CONVENTION: Following
    10. CALENDAR: USD Calendar
    """
    
    print("Testing Contract Parser...")
    print("=" * 50)
    
    # Test the parser directly
    parser = ContractParser()
    extraction = parser.parse_contract(sample_text)
    
    print(f"Instrument Type: {extraction.instrument_type}")
    print(f"Overall Confidence: {extraction.overall_confidence:.2f}")
    print(f"Number of Fields Extracted: {len(extraction.fields)}")
    print()
    
    print("Extracted Fields:")
    print("-" * 30)
    for field in extraction.fields:
        print(f"Field: {field.field_name}")
        print(f"  Value: {field.value}")
        print(f"  Confidence: {field.confidence:.2f}")
        print(f"  Source: {field.source_text}")
        print()
    
    # Test validation
    is_valid, issues = parser.validate_extraction(extraction)
    print(f"Validation Result: {'VALID' if is_valid else 'INVALID'}")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"  - {issue}")
    print()
    
    # Test the LangGraph node function
    print("Testing LangGraph Node Function...")
    print("=" * 50)
    
    node_result = parse_contract_node(sample_text)
    
    print(f"Node Result Keys: {list(node_result.keys())}")
    print(f"Fields Count: {len(node_result['fields'])}")
    print(f"Instrument Type: {node_result['instrument_type']}")
    print(f"Overall Confidence: {node_result['overall_confidence']:.2f}")
    print(f"Is Valid: {node_result['is_valid']}")
    
    if node_result['issues']:
        print("Issues:")
        for issue in node_result['issues']:
            print(f"  - {issue}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_contract_parser()



