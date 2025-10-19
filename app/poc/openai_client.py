"""OpenAI client wrapper for PoC."""

import json
import httpx
from typing import Dict, Any
from app.settings import get_settings


class OpenAIClient:
    """Simple wrapper for OpenAI API calls."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
    
    async def call_llm(
        self,
        system_prompt: str,
        user_json: Dict[str, Any],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """Call OpenAI API with structured prompts."""
        
        if not self.settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")
        
        model = model or self.settings.OPENAI_MODEL
        temperature = temperature if temperature is not None else self.settings.LLM_TEMPERATURE
        max_tokens = max_tokens or self.settings.MAX_OUTPUT_TOKENS
        
        # Ensure temperature is within safe bounds
        temperature = max(0.0, min(0.1, temperature))
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_json)}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Validate JSON response
                try:
                    json.loads(content)
                    return content
                except json.JSONDecodeError:
                    raise ValueError(f"LLM returned invalid JSON: {content}")
                    
            except httpx.HTTPStatusError as e:
                raise ValueError(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
            except httpx.RequestError as e:
                raise ValueError(f"Request error: {str(e)}")
    
    async def call_llm_with_retry(
        self,
        system_prompt: str,
        user_json: Dict[str, Any],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        max_retries: int = 3
    ) -> str:
        """Call LLM with retry logic."""
        
        for attempt in range(max_retries):
            try:
                return await self.call_llm(
                    system_prompt=system_prompt,
                    user_json=user_json,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                # Wait before retry (exponential backoff)
                import asyncio
                await asyncio.sleep(2 ** attempt)
        
        raise ValueError("Max retries exceeded")


# Global client instance
openai_client = OpenAIClient()
