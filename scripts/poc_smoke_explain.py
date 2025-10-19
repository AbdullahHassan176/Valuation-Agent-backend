#!/usr/bin/env python3
"""Smoke test for run explanation PoC endpoint."""

import asyncio
import httpx
import json
import sys


async def test_explain_run():
    """Test run explanation endpoint."""
    
    # Get run_id from command line or use default
    run_id = sys.argv[1] if len(sys.argv) > 1 else "run-001"
    api_base = "http://localhost:9000"  # API service base URL
    
    test_data = {
        "run_id": run_id,
        "api_base": api_base,
        "extra_context": "This is a test explanation request",
        "sources": [
            {
                "source_id": "ifrs13_demo",
                "section": "measurement",
                "text": "Fair value is the price that would be received to sell an asset or paid to transfer a liability in an orderly transaction between market participants at the measurement date."
            }
        ]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/poc/explain_run",
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
                    narrative = result.get("narrative", "")
                    assert len(narrative) > 10, "OK status requires substantial narrative"
                    print(f"✅ Explain run test passed - narrative length: {len(narrative)}")
                    print(f"Narrative: {narrative[:200]}...")
                else:
                    print("✅ Explain run test passed - ABSTAIN response (acceptable)")
            else:
                print(f"❌ Explain run test failed - HTTP {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Explain run test failed with exception: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_explain_run())
