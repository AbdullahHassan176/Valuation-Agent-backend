"""
Policy management router for runtime policy configuration.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import yaml
import os
from pathlib import Path

from app.deps import require_api_key

router = APIRouter(prefix="/policy", tags=["policy"])

# Runtime policy overrides (in-memory for PoC)
_runtime_overrides: Dict[str, Any] = {}

class PolicyUpdate(BaseModel):
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum confidence threshold")
    require_citations: Optional[bool] = Field(None, description="Whether citations are required")
    disallow_language: Optional[List[str]] = Field(None, description="List of disallowed language tags")
    restricted_advice: Optional[List[str]] = Field(None, description="List of restricted advice tags")

class PolicyResponse(BaseModel):
    min_confidence: float
    require_citations: bool
    disallow_language: List[str]
    restricted_advice: List[str]
    source: str  # "file" or "runtime"

def load_policy_file() -> Dict[str, Any]:
    """Load policy configuration from YAML file."""
    policy_file = Path("app/policy/policies.yml")
    
    if not policy_file.exists():
        # Return default policy if file doesn't exist
        return {
            "min_confidence": 0.7,
            "require_citations": True,
            "disallow_language": ["unprofessional", "offensive"],
            "restricted_advice": ["investment", "legal"]
        }
    
    try:
        with open(policy_file, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load policy file: {str(e)}")

def get_effective_policy() -> Dict[str, Any]:
    """Get effective policy (file + runtime overrides)."""
    file_policy = load_policy_file()
    
    # Apply runtime overrides
    effective_policy = file_policy.copy()
    effective_policy.update(_runtime_overrides)
    
    return effective_policy

@router.get("", response_model=PolicyResponse)
async def get_policy(_: bool = Depends(require_api_key)):
    """
    Get current policy configuration.
    Returns the effective policy (file + runtime overrides).
    """
    try:
        policy = get_effective_policy()
        
        return PolicyResponse(
            min_confidence=policy.get("min_confidence", 0.7),
            require_citations=policy.get("require_citations", True),
            disallow_language=policy.get("disallow_language", []),
            restricted_advice=policy.get("restricted_advice", []),
            source="runtime" if _runtime_overrides else "file"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get policy: {str(e)}")

@router.put("", response_model=PolicyResponse)
async def update_policy(
    policy_update: PolicyUpdate,
    _: bool = Depends(require_api_key)
):
    """
    Update policy configuration (runtime overrides).
    This is a PoC implementation that stores overrides in memory.
    """
    try:
        # Update runtime overrides
        if policy_update.min_confidence is not None:
            _runtime_overrides["min_confidence"] = policy_update.min_confidence
        
        if policy_update.require_citations is not None:
            _runtime_overrides["require_citations"] = policy_update.require_citations
        
        if policy_update.disallow_language is not None:
            _runtime_overrides["disallow_language"] = policy_update.disallow_language
        
        if policy_update.restricted_advice is not None:
            _runtime_overrides["restricted_advice"] = policy_update.restricted_advice
        
        # Return updated policy
        policy = get_effective_policy()
        
        return PolicyResponse(
            min_confidence=policy.get("min_confidence", 0.7),
            require_citations=policy.get("require_citations", True),
            disallow_language=policy.get("disallow_language", []),
            restricted_advice=policy.get("restricted_advice", []),
            source="runtime"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update policy: {str(e)}")

@router.delete("")
async def reset_policy(_: bool = Depends(require_api_key)):
    """
    Reset policy to file defaults (clear runtime overrides).
    """
    global _runtime_overrides
    _runtime_overrides.clear()
    
    return {"message": "Policy reset to file defaults"}

@router.get("/status")
async def get_policy_status(_: bool = Depends(require_api_key)):
    """
    Get policy status information.
    """
    return {
        "has_runtime_overrides": bool(_runtime_overrides),
        "runtime_overrides": _runtime_overrides,
        "policy_file_exists": Path("app/policy/policies.yml").exists()
    }
