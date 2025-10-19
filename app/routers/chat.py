"""Chat agent endpoints with SSE streaming."""

import json
import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.chat_graph import process_chat_message, ChatResponse
from app.settings import get_settings, Settings
from app.deps import require_api_key

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat messages."""
    
    message: str
    doc_id: Optional[str] = None
    standard: Optional[str] = None


class ChatResponseModel(BaseModel):
    """Response model for chat messages."""
    
    message: str
    citations: list
    confidence: float
    tool_used: Optional[str] = None
    status: str


async def stream_chat_response(message: str, doc_id: Optional[str] = None, standard: Optional[str] = None):
    """Stream chat response with SSE events.
    
    Args:
        message: User message
        doc_id: Optional document ID
        standard: Optional IFRS standard
        
    Yields:
        SSE events for streaming response
    """
    try:
        # Send tool call event
        yield f"data: {json.dumps({'event': 'TOOL_CALLED', 'data': {'message': 'Processing your request...'}})}\n\n"
        
        # Process the message
        response = process_chat_message(message, doc_id, standard)
        
        # Send tool used event
        if response.tool_used:
            yield f"data: {json.dumps({'event': 'TOOL_CALLED', 'data': {'tool': response.tool_used, 'message': f'Using {response.tool_used} tool...'}})}\n\n"
        
        # Stream response tokens (simulate streaming by splitting into words)
        words = response.message.split()
        for i, word in enumerate(words):
            # Add some delay to simulate streaming
            await asyncio.sleep(0.05)
            
            # Send token event
            yield f"data: {json.dumps({'event': 'TOKEN', 'data': {'token': word + ' ', 'position': i + 1, 'total': len(words)}})}\n\n"
        
        # Send citations event
        if response.citations:
            yield f"data: {json.dumps({'event': 'CITATIONS', 'data': {'citations': [{'standard': c.standard, 'paragraph': c.paragraph, 'section': c.section} for c in response.citations]}})}\n\n"
        
        # Send confidence event
        yield f"data: {json.dumps({'event': 'CONFIDENCE', 'data': {'confidence': response.confidence, 'status': response.status}})}\n\n"
        
        # Send done event
        yield f"data: {json.dumps({'event': 'DONE', 'data': {'message': 'Response complete', 'tool_used': response.tool_used, 'status': response.status}})}\n\n"
        
    except Exception as e:
        # Send error event
        yield f"data: {json.dumps({'event': 'ERROR', 'data': {'error': str(e)}})}\n\n"


@router.post("/chat", response_model=ChatResponseModel)
async def chat_message(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
    _: bool = Depends(require_api_key)
) -> ChatResponseModel:
    """Send a chat message and get response.
    
    Args:
        request: Chat request with message and optional parameters
        settings: Application settings
        
    Returns:
        Chat response with validated answer
        
    Raises:
        HTTPException: If chat processing fails
    """
    try:
        if not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )
        
        # Process the message
        response = process_chat_message(
            message=request.message,
            doc_id=request.doc_id,
            standard=request.standard
        )
        
        return ChatResponseModel(
            message=response.message,
            citations=[{"standard": c.standard, "paragraph": c.paragraph, "section": c.section} for c in response.citations],
            confidence=response.confidence,
            tool_used=response.tool_used,
            status=response.status
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )


@router.get("/chat/stream")
async def stream_chat(
    message: str,
    doc_id: Optional[str] = None,
    standard: Optional[str] = None,
    settings: Settings = Depends(get_settings),
    _: bool = Depends(require_api_key)
) -> StreamingResponse:
    """Stream chat response with Server-Sent Events.
    
    Args:
        message: User message
        doc_id: Optional document ID
        standard: Optional IFRS standard
        settings: Application settings
        
    Returns:
        StreamingResponse with SSE events
        
    Raises:
        HTTPException: If streaming fails
    """
    try:
        if not message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )
        
        return StreamingResponse(
            stream_chat_response(message, doc_id, standard),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error streaming chat response: {str(e)}"
        )


@router.get("/chat/health")
async def chat_health_check() -> dict:
    """Health check for chat service.
    
    Returns:
        Service status information
    """
    return {
        "status": "healthy",
        "service": "chat-agent",
        "message": "Constrained chat agent is running",
        "capabilities": [
            "IFRS question answering",
            "Document analysis",
            "Document search",
            "Policy-validated responses"
        ],
        "tools": [
            "ifrs_ask",
            "analyze_document", 
            "search_documents"
        ]
    }


@router.get("/chat/tools")
async def get_chat_tools() -> dict:
    """Get information about available chat tools.
    
    Returns:
        Available tools and their descriptions
    """
    from app.agents.tools import get_available_tools
    return get_available_tools()


@router.get("/chat/intent")
async def classify_intent(message: str) -> dict:
    """Classify user intent from message.
    
    Args:
        message: User message to classify
        
    Returns:
        Intent classification result
    """
    try:
        from app.agents.chat_graph import chat_agent
        intent = chat_agent.classify_intent(message)
        
        return {
            "message": message,
            "intent": intent,
            "confidence": 1.0 if intent != "unknown" else 0.0,
            "description": {
                "ask_ifrs": "Ask questions about IFRS standards",
                "analyze_doc": "Analyze documents for IFRS compliance", 
                "search_docs": "Search for available documents",
                "unknown": "Intent not recognized - guidance will be provided"
            }.get(intent, "Unknown intent")
        }
        
    except Exception as e:
        return {
            "message": message,
            "intent": "error",
            "confidence": 0.0,
            "error": str(e)
        }
