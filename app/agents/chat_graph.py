"""LangGraph-based chat agent with tool constraints."""

import re
from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass
from app.agents.tools import tool_ifrs_ask, tool_analyze_document, tool_search_documents
from app.agents.guards import apply_policy
from app.agents.schemas import IFRSAnswer, Citation
from app.agents.feedback import Feedback


@dataclass
class ChatMessage:
    """Chat message with metadata."""
    
    content: str
    role: Literal["user", "assistant", "system"]
    tool_calls: Optional[List[Dict[str, Any]]] = None
    citations: Optional[List[Citation]] = None
    confidence: Optional[float] = None


@dataclass
class ChatResponse:
    """Chat response with validation."""
    
    message: str
    citations: List[Citation]
    confidence: float
    tool_used: Optional[str] = None
    status: str = "OK"


class ChatAgent:
    """Constrained chat agent that only uses tools."""
    
    def __init__(self):
        """Initialize chat agent."""
        self.intent_patterns = {
            "ask_ifrs": [
                r"what is.*ifrs",
                r"explain.*ifrs",
                r"how does.*ifrs",
                r"ifrs.*requirement",
                r"fair value.*measurement",
                r"hierarchy.*level",
                r"market.*participant",
                r"day.*1.*p&l",
                r"non.*performance.*risk",
                r"observable.*input"
            ],
            "analyze_doc": [
                r"analyze.*document",
                r"check.*document",
                r"review.*document", 
                r"feedback.*document",
                r"compliance.*document",
                r"document.*analysis",
                r"document.*review"
            ],
            "search_docs": [
                r"search.*document",
                r"find.*document",
                r"list.*document",
                r"show.*document",
                r"what.*document",
                r"available.*document",
                r"document.*available"
            ]
        }
    
    def classify_intent(self, message: str) -> str:
        """Classify user intent from message.
        
        Args:
            message: User message
            
        Returns:
            Intent classification: "ask_ifrs", "analyze_doc", "search_docs", or "unknown"
        """
        message_lower = message.lower()
        
        # Check for each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        return "unknown"
    
    def handle_ask_ifrs(self, message: str, doc_id: Optional[str] = None, standard: Optional[str] = None) -> ChatResponse:
        """Handle IFRS question intent.
        
        Args:
            message: User message
            doc_id: Optional document ID
            standard: Optional IFRS standard filter
            
        Returns:
            Chat response with IFRS answer
        """
        try:
            # Use IFRS tool
            answer = tool_ifrs_ask(message, standard)
            
            # Apply policy guardrails
            validated_answer = apply_policy(answer)
            
            return ChatResponse(
                message=validated_answer.answer,
                citations=validated_answer.citations,
                confidence=validated_answer.confidence,
                tool_used="ifrs_ask",
                status=validated_answer.status
            )
            
        except Exception as e:
            return ChatResponse(
                message=f"Error processing IFRS question: {str(e)}",
                citations=[],
                confidence=0.0,
                tool_used="ifrs_ask",
                status="ABSTAIN"
            )
    
    def handle_analyze_doc(self, message: str, doc_id: Optional[str] = None, standard: Optional[str] = None) -> ChatResponse:
        """Handle document analysis intent.
        
        Args:
            message: User message
            doc_id: Document ID (required for analysis)
            standard: IFRS standard (default: IFRS 13)
            
        Returns:
            Chat response with document analysis
        """
        try:
            if not doc_id:
                return ChatResponse(
                    message="Document analysis requires a document ID. Please specify which document to analyze.",
                    citations=[],
                    confidence=0.0,
                    tool_used="analyze_document",
                    status="ABSTAIN"
                )
            
            # Use document analysis tool
            feedback = tool_analyze_document(doc_id, standard or "IFRS 13")
            
            # Create response message
            response_parts = [feedback.summary]
            
            if feedback.items:
                response_parts.append(f"\n\nChecklist Results ({len(feedback.items)} items):")
                for i, item in enumerate(feedback.items[:5], 1):  # Show first 5 items
                    status_icon = "✅" if item.met else "❌"
                    response_parts.append(f"{i}. {status_icon} {item.description}")
            
            # Extract citations from feedback items
            all_citations = []
            for item in feedback.items:
                all_citations.extend(item.citations)
            
            return ChatResponse(
                message="\n".join(response_parts),
                citations=all_citations,
                confidence=feedback.confidence,
                tool_used="analyze_document",
                status=feedback.status
            )
            
        except Exception as e:
            return ChatResponse(
                message=f"Error analyzing document: {str(e)}",
                citations=[],
                confidence=0.0,
                tool_used="analyze_document",
                status="ABSTAIN"
            )
    
    def handle_search_docs(self, message: str, doc_id: Optional[str] = None, standard: Optional[str] = None) -> ChatResponse:
        """Handle document search intent.
        
        Args:
            message: User message
            doc_id: Optional document ID
            standard: Optional IFRS standard
            
        Returns:
            Chat response with document search results
        """
        try:
            # Extract search term from message
            search_term = message.lower()
            
            # Remove common search words
            search_words = ["search", "find", "list", "show", "document", "documents"]
            for word in search_words:
                search_term = search_term.replace(word, "")
            
            search_term = search_term.strip()
            if not search_term:
                search_term = "valuation"  # Default search term
            
            # Use document search tool
            results = tool_search_documents(search_term)
            
            if not results:
                return ChatResponse(
                    message="No documents found matching your search criteria.",
                    citations=[],
                    confidence=0.0,
                    tool_used="search_documents",
                    status="OK"
                )
            
            # Create response message
            response_parts = [f"Found {len(results)} documents:"]
            
            for i, doc in enumerate(results, 1):
                tags_str = ", ".join(doc.get("tags", [])) if doc.get("tags") else "No tags"
                response_parts.append(f"{i}. {doc.get('title', 'Untitled')} (ID: {doc.get('doc_id', 'N/A')})")
                response_parts.append(f"   Tags: {tags_str}")
            
            return ChatResponse(
                message="\n".join(response_parts),
                citations=[],
                confidence=1.0,
                tool_used="search_documents",
                status="OK"
            )
            
        except Exception as e:
            return ChatResponse(
                message=f"Error searching documents: {str(e)}",
                citations=[],
                confidence=0.0,
                tool_used="search_documents",
                status="ABSTAIN"
            )
    
    def handle_unknown_intent(self, message: str) -> ChatResponse:
        """Handle unknown intent.
        
        Args:
            message: User message
            
        Returns:
            Chat response with guidance
        """
        guidance = """I can only help with specific tasks using my available tools:

1. **Ask IFRS Questions**: Ask about IFRS standards, fair value measurement, hierarchy levels, etc.
   Example: "What is fair value measurement according to IFRS 13?"

2. **Analyze Documents**: Analyze uploaded documents for IFRS compliance.
   Example: "Analyze document valuation-memo-2023 for IFRS 13 compliance"

3. **Search Documents**: Find and list available documents.
   Example: "Search for valuation documents" or "List available documents"

Please rephrase your question to use one of these capabilities."""
        
        return ChatResponse(
            message=guidance,
            citations=[],
            confidence=0.0,
            tool_used=None,
            status="ABSTAIN"
        )
    
    def process_message(self, message: str, doc_id: Optional[str] = None, standard: Optional[str] = None) -> ChatResponse:
        """Process user message and return response.
        
        Args:
            message: User message
            doc_id: Optional document ID
            standard: Optional IFRS standard
            
        Returns:
            Chat response with validated answer
        """
        # Classify intent
        intent = self.classify_intent(message)
        
        # Route to appropriate handler
        if intent == "ask_ifrs":
            return self.handle_ask_ifrs(message, doc_id, standard)
        elif intent == "analyze_doc":
            return self.handle_analyze_doc(message, doc_id, standard)
        elif intent == "search_docs":
            return self.handle_search_docs(message, doc_id, standard)
        else:
            return self.handle_unknown_intent(message)


# Global chat agent instance
chat_agent = ChatAgent()


def process_chat_message(message: str, doc_id: Optional[str] = None, standard: Optional[str] = None) -> ChatResponse:
    """Process a chat message and return response.
    
    Args:
        message: User message
        doc_id: Optional document ID
        standard: Optional IFRS standard
        
    Returns:
        Chat response with validated answer
    """
    return chat_agent.process_message(message, doc_id, standard)
