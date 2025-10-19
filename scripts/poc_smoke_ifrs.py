#!/usr/bin/env python3
"""Smoke test for IFRS PoC endpoint."""

import asyncio
import httpx
import json


async def test_ifrs_ask():
    """Test IFRS ask endpoint."""
    
    # Test data
    test_data = {
        "question": "What distinguishes Level 2 vs Level 3 in the fair value hierarchy?",
        "sources": [
            {
                "source_id": "ifrs13_demo",
                "section": "hierarchy",
                "text": "IFRS 13 establishes a fair value hierarchy that categorizes the inputs to valuation techniques into three levels. Level 1 inputs are quoted prices in active markets for identical assets or liabilities. Level 2 inputs are inputs other than quoted prices included within Level 1 that are observable for the asset or liability. Level 3 inputs are unobservable inputs for the asset or liability."
            }
        ]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/poc/ifrs_ask",
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
                    assert len(result.get("citations", [])) > 0, "OK status requires citations"
                    assert result.get("confidence", 0) >= 0.7, f"Confidence {result.get('confidence')} below 0.7"
                    print("✅ IFRS ask test passed - OK response with citations and confidence")
                else:
                    print("✅ IFRS ask test passed - ABSTAIN response (acceptable)")
            else:
                print(f"❌ IFRS ask test failed - HTTP {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"❌ IFRS ask test failed with exception: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_ifrs_ask())
