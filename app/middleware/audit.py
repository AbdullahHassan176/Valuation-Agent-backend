"""Audit middleware for logging requests and interactions."""

import time
import json
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.settings import settings
from app.audit.models import log_interaction
from app.utils.sanitization import sanitize_log_entry


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for auditing API requests and interactions."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log audit information."""
        start_time = time.time()
        
        # Extract user from header if present
        user = request.headers.get("X-USER", "anonymous")
        
        # Get request body size (if available)
        body_size = 0
        if hasattr(request, "_body"):
            body_size = len(request._body) if request._body else 0
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log audit information (PoC: stdout, later wire to DB)
        audit_log = {
            "timestamp": time.time(),
            "path": str(request.url.path),
            "method": request.method,
            "user": user,
            "status_code": response.status_code,
            "body_size": body_size,
            "process_time": round(process_time, 4),
            "user_agent": request.headers.get("user-agent", ""),
            "remote_addr": request.client.host if request.client else "unknown"
        }
        
        # Sanitize audit log for PII
        sanitized_log, redaction_log = sanitize_log_entry(json.dumps(audit_log))
        
        # Print sanitized audit log
        print(f"AUDIT: {sanitized_log}")
        
        # Log redactions if any
        if redaction_log:
            redaction_summary = ', '.join([f"{r['count']} {r['type']}" for r in redaction_log])
            print(f"PII_REDACTED: {redaction_summary}")
        
        # Log interaction if this is an interaction endpoint
        if self._is_interaction_endpoint(request.url.path):
            try:
                await self._log_interaction(request, response, user)
            except Exception as e:
                print(f"ERROR LOGGING INTERACTION: {e}")
        
        return response
    
    def _is_interaction_endpoint(self, path: str) -> bool:
        """Check if the endpoint is an interaction endpoint.
        
        Args:
            path: Request path
            
        Returns:
            True if interaction endpoint
        """
        interaction_endpoints = [
            "/api/v1/ifrs/ask",
            "/api/v1/chat",
            "/api/v1/feedback/analyze"
        ]
        return any(path.startswith(endpoint) for endpoint in interaction_endpoints)
    
    async def _log_interaction(self, request: Request, response: Response, user: str):
        """Log interaction details.
        
        Args:
            request: Incoming request
            response: Response from handler
            user: User identifier
        """
        try:
            # Get request body
            request_body = await request.body()
            request_data = json.loads(request_body) if request_body else {}
            
            # Get response body
            response_body = b""
            if hasattr(response, "body"):
                response_body = response.body
            elif hasattr(response, "_body"):
                response_body = response._body
            
            response_data = json.loads(response_body) if response_body else {}
            
            # Extract interaction data based on endpoint
            if request.url.path.startswith("/api/v1/ifrs/ask"):
                await self._log_ifrs_interaction(request_data, response_data, user)
            elif request.url.path.startswith("/api/v1/chat"):
                await self._log_chat_interaction(request_data, response_data, user)
            elif request.url.path.startswith("/api/v1/feedback/analyze"):
                await self._log_feedback_interaction(request_data, response_data, user)
                
        except Exception as e:
            print(f"ERROR LOGGING INTERACTION: {e}")
    
    async def _log_ifrs_interaction(self, request_data: dict, response_data: dict, user: str):
        """Log IFRS interaction.
        
        Args:
            request_data: Request data
            response_data: Response data
            user: User identifier
        """
        interaction_id = log_interaction(
            user=user,
            question=request_data.get("question", ""),
            intent="ask_ifrs",
            response=response_data.get("answer", ""),
            status=response_data.get("status", "ABSTAIN"),
            confidence=response_data.get("confidence", 0.0),
            model="valuation-agent",
            vector_dir=settings.VECTOR_DIR,
            tool_used="ifrs_ask",
            citations=response_data.get("citations", []),
            documents=[]
        )
        print(f"IFRS INTERACTION LOGGED: ID {interaction_id}")
    
    async def _log_chat_interaction(self, request_data: dict, response_data: dict, user: str):
        """Log chat interaction.
        
        Args:
            request_data: Request data
            response_data: Response data
            user: User identifier
        """
        interaction_id = log_interaction(
            user=user,
            question=request_data.get("message", ""),
            intent="chat",
            response=response_data.get("message", ""),
            status=response_data.get("status", "ABSTAIN"),
            confidence=response_data.get("confidence", 0.0),
            model="valuation-agent",
            vector_dir=settings.VECTOR_DIR,
            tool_used=response_data.get("tool_used"),
            doc_id=request_data.get("doc_id"),
            citations=response_data.get("citations", []),
            documents=[]
        )
        print(f"CHAT INTERACTION LOGGED: ID {interaction_id}")
    
    async def _log_feedback_interaction(self, request_data: dict, response_data: dict, user: str):
        """Log feedback interaction.
        
        Args:
            request_data: Request data
            response_data: Response data
            user: User identifier
        """
        # Extract citations from feedback items
        citations = []
        items = response_data.get("items", [])
        for item in items:
            item_citations = item.get("citations", [])
            for citation in item_citations:
                citations.append({
                    "standard": citation.get("standard", ""),
                    "paragraph": citation.get("paragraph", ""),
                    "section": citation.get("section")
                })
        
        interaction_id = log_interaction(
            user=user,
            question=f"Analyze document {request_data.get('doc_id', '')} for {request_data.get('standard', 'IFRS 13')} compliance",
            intent="analyze_doc",
            response=response_data.get("summary", ""),
            status=response_data.get("status", "ABSTAIN"),
            confidence=response_data.get("confidence", 0.0),
            model="valuation-agent",
            vector_dir=settings.VECTOR_DIR,
            tool_used="analyze_document",
            doc_id=request_data.get("doc_id"),
            citations=citations,
            documents=[request_data.get("doc_id")] if request_data.get("doc_id") else []
        )
        print(f"FEEDBACK INTERACTION LOGGED: ID {interaction_id}")
