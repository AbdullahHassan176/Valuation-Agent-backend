"""
Chat endpoint with SSE streaming for constrained chat agent
"""

import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from datetime import datetime
import uuid

from agents.chat import chat_agent

router = APIRouter(prefix="/chat", tags=["chat"])


async def generate_chat_stream(run_id: str, message: str):
    """Generate SSE stream for chat responses"""
    try:
        # Send initial message
        yield f"data: {json.dumps({'type': 'message', 'content': 'Processing your request...', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
        
        # Parse and execute the request
        result = await chat_agent.process_message(message, run_id)
        
        # Send tool call information
        yield f"data: {json.dumps({'type': 'tool_call', 'tool': result.get('tool_call'), 'parameters': result.get('tool_parameters'), 'timestamp': datetime.utcnow().isoformat()})}\n\n"
        
        # Send tool result
        yield f"data: {json.dumps({'type': 'tool_result', 'result': result.get('result'), 'timestamp': datetime.utcnow().isoformat()})}\n\n"
        
        # Send final response
        yield f"data: {json.dumps({'type': 'response', 'content': result.get('response'), 'timestamp': datetime.utcnow().isoformat()})}\n\n"
        
        # Send completion signal
        yield f"data: {json.dumps({'type': 'complete', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
        
    except Exception as e:
        # Send error
        yield f"data: {json.dumps({'type': 'error', 'content': f'Chat processing failed: {str(e)}', 'timestamp': datetime.utcnow().isoformat()})}\n\n"


@router.get("/{run_id}/stream")
async def chat_stream(run_id: str, message: str):
    """
    Chat endpoint with SSE streaming
    
    Args:
        run_id: Run identifier
        message: User message
        
    Returns:
        SSE stream with chat responses
    """
    try:
        # Validate run_id format (basic check)
        if not run_id or len(run_id) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid run_id format"
            )
        
        # Validate message
        if not message or len(message.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        # Limit message length
        if len(message) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message too long (max 1000 characters)"
            )
        
        return StreamingResponse(
            generate_chat_stream(run_id, message.strip()),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat service error: {str(e)}"
        )


@router.post("/{run_id}")
async def chat_message(run_id: str, request: Dict[str, Any]):
    """
    Non-streaming chat endpoint
    
    Args:
        run_id: Run identifier
        request: Chat request with message
        
    Returns:
        Chat response
    """
    try:
        message = request.get("message", "")
        if not message or len(message.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        # Process the message
        result = await chat_agent.process_message(message.strip(), run_id)
        
        return {
            "run_id": run_id,
            "message": message,
            "response": result.get("response"),
            "tool_call": result.get("tool_call"),
            "tool_parameters": result.get("tool_parameters"),
            "timestamp": result.get("timestamp"),
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing error: {str(e)}"
        )


@router.get("/{run_id}/examples")
async def get_chat_examples(run_id: str):
    """
    Get example chat messages for a run
    
    Args:
        run_id: Run identifier
        
    Returns:
        List of example messages
    """
    return {
        "run_id": run_id,
        "examples": [
            {
                "category": "Run Status",
                "messages": [
                    "Show me the run status",
                    "What's the current state?",
                    "Is the run completed?"
                ]
            },
            {
                "category": "Sensitivity Analysis",
                "messages": [
                    "Show me parallel +1bp sensitivity",
                    "Run sensitivity with -10bp shock",
                    "What's the PV01 for this trade?"
                ]
            },
            {
                "category": "Explanations",
                "messages": [
                    "Explain this valuation",
                    "Why is this Level 2?",
                    "What methodology was used?"
                ]
            },
            {
                "category": "Export",
                "messages": [
                    "Export Excel now",
                    "Generate the report",
                    "Download the results"
                ]
            }
        ],
        "guidance": "I can help you with run status, sensitivity analysis, explanations, and exports. I cannot price new instruments or perform calculations outside the allowed scope."
    }


@router.get("/{run_id}/capabilities")
async def get_chat_capabilities(run_id: str):
    """
    Get chat agent capabilities
    
    Args:
        run_id: Run identifier
        
    Returns:
        Chat agent capabilities
    """
    return {
        "run_id": run_id,
        "capabilities": {
            "get_run_status": {
                "description": "Get the status and details of a valuation run",
                "example": "Show me the run status"
            },
            "run_sensitivity": {
                "description": "Run sensitivity analysis on a valuation run",
                "example": "Show me parallel +1bp sensitivity"
            },
            "explain_run": {
                "description": "Get an explanation of a valuation run using RAG",
                "example": "Explain this valuation"
            }
        },
        "limitations": [
            "Cannot price new instruments",
            "Cannot perform calculations outside allowed scope",
            "Cannot invent or fabricate numbers",
            "Cannot create new derivatives or exotic products"
        ],
        "abstain_triggers": [
            "Requests to price instruments",
            "Requests to calculate values",
            "Requests to invent numbers",
            "Requests for exotic derivatives"
        ]
    }
