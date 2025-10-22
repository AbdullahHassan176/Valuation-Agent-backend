#!/usr/bin/env python3
"""
Test script to verify Groq deployment configuration
"""

import os
import sys
import asyncio
import aiohttp
from pathlib import Path

def test_environment_variables():
    """Test if Groq environment variables are set."""
    print("🔍 Testing Groq Environment Variables:")
    print(f"   - USE_GROQ: {os.getenv('USE_GROQ', 'Not set')}")
    print(f"   - GROQ_API_KEY: {'Set' if os.getenv('GROQ_API_KEY') else 'Not set'}")
    print(f"   - GROQ_BASE_URL: {os.getenv('GROQ_BASE_URL', 'Not set')}")
    print(f"   - GROQ_MODEL: {os.getenv('GROQ_MODEL', 'Not set')}")
    
    # Check if all required variables are set
    required_vars = ['USE_GROQ', 'GROQ_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

async def test_groq_api():
    """Test Groq API connectivity."""
    groq_api_key = os.getenv('GROQ_API_KEY')
    groq_base_url = os.getenv('GROQ_BASE_URL', 'https://api.groq.com/openai/v1')
    groq_model = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')
    
    if not groq_api_key:
        print("❌ GROQ_API_KEY not set")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": groq_model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! Please respond with 'Groq is working!'"}
            ],
            "temperature": 0.7,
            "max_tokens": 50
        }
        
        print(f"🔍 Testing Groq API connection...")
        print(f"   - URL: {groq_base_url}/chat/completions")
        print(f"   - Model: {groq_model}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{groq_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data["choices"][0]["message"]["content"]
                    print(f"✅ Groq API test successful!")
                    print(f"   - Response: {response_text}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Groq API error: {response.status}")
                    print(f"   - Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Groq API test failed: {e}")
        return False

async def test_local_endpoints():
    """Test local endpoints if the app is running."""
    try:
        base_url = "http://localhost:8000"
        
        # Test health endpoint
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/healthz") as response:
                if response.status == 200:
                    print("✅ Health endpoint working")
                else:
                    print(f"❌ Health endpoint failed: {response.status}")
                    return False
            
            # Test Groq config endpoint
            async with session.get(f"{base_url}/api/test/groq-config") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Groq config endpoint working")
                    print(f"   - Config: {data}")
                    return True
                else:
                    print(f"❌ Groq config endpoint failed: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Local endpoint test failed: {e}")
        return False

def print_azure_setup_instructions():
    """Print instructions for setting up Azure environment variables."""
    print("\n" + "="*60)
    print("🔧 AZURE ENVIRONMENT VARIABLES SETUP")
    print("="*60)
    print("1. Go to Azure Portal:")
    print("   - Navigate to your App Service")
    print("   - Click 'Configuration' under Settings")
    print("   - Click 'Application settings' tab")
    print("")
    print("2. Add these environment variables:")
    print("   - Name: USE_GROQ, Value: true")
    print("   - Name: GROQ_API_KEY, Value: your_groq_key_here")
    print("   - Name: GROQ_MODEL, Value: llama-3.1-8b-instant")
    print("   - Name: GROQ_BASE_URL, Value: https://api.groq.com/openai/v1")
    print("")
    print("3. Get your Groq API key:")
    print("   - Go to: https://console.groq.com/")
    print("   - Sign up (free, no credit card)")
    print("   - Create API key")
    print("   - Copy the key (starts with 'gsk_...')")
    print("")
    print("4. Save and restart your App Service")
    print("="*60)

async def main():
    """Main test function."""
    print("🚀 Groq Deployment Test")
    print("="*40)
    
    # Test 1: Environment variables
    env_ok = test_environment_variables()
    
    # Test 2: Groq API (if env vars are set)
    if env_ok:
        groq_ok = await test_groq_api()
    else:
        groq_ok = False
        print("⏭️ Skipping Groq API test (env vars not set)")
    
    # Test 3: Local endpoints (if app is running)
    print("\n🔍 Testing local endpoints...")
    local_ok = await test_local_endpoints()
    
    # Summary
    print("\n" + "="*40)
    print("📊 TEST SUMMARY")
    print("="*40)
    print(f"Environment Variables: {'✅' if env_ok else '❌'}")
    print(f"Groq API Connection: {'✅' if groq_ok else '❌'}")
    print(f"Local Endpoints: {'✅' if local_ok else '❌'}")
    
    if not env_ok:
        print_azure_setup_instructions()
    
    if env_ok and groq_ok:
        print("\n🎉 Groq is properly configured!")
    else:
        print("\n⚠️ Groq configuration needs attention")

if __name__ == "__main__":
    asyncio.run(main())
