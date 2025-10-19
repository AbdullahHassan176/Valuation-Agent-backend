#!/usr/bin/env python3
"""Smoke test for contract parsing PoC endpoint."""

import asyncio
import httpx
import json


async def test_parse_contract():
    """Test contract parsing endpoint."""
    
    # Test data - synthetic term sheet
    test_data = {
        "text": """
        INTEREST RATE SWAP TERM SHEET
        
        Trade Date: 2024-01-15
        Effective Date: 2024-01-17
        Maturity Date: 2029-01-17
        Notional Amount: USD 10,000,000
        Fixed Rate: 3.25% per annum
        Floating Rate: SOFR + 0.25%
        Payment Frequency: Quarterly
        Day Count Convention: ACT/360
        Business Day Convention: Modified Following
        
        Counterparties:
        - Party A: ABC Bank
        - Party B: XYZ Corporation
        
        This is a standard interest rate swap where Party A pays fixed and Party B pays floating.
        """,
        "instrument_hint": "IRS",
        "ccy_hint": "USD"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/poc/parse_contract",
                json=test_data,
                timeout=30.0
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("Response JSON:")
                print(json.dumps(result, indent=2))
                
                # Validate response structure
                assert result.get("status") in ["OK", "ABSTAIN"], f"Invalid status: {result.get('status')}"
                
                if result.get("status") == "OK":
                    fields = result.get("fields", [])
                    assert len(fields) > 0, "OK status requires extracted fields"
                    print(f"✅ Parse contract test passed - extracted {len(fields)} fields")
                    
                    # Print extracted fields
                    for field in fields:
                        print(f"  - {field.get('key')}: {field.get('value')} (confidence: {field.get('confidence')})")
                else:
                    print("✅ Parse contract test passed - ABSTAIN response (acceptable)")
            else:
                print(f"❌ Parse contract test failed - HTTP {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Parse contract test failed with exception: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_parse_contract())
