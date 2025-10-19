"""Document feedback analysis against IFRS standards."""

import yaml
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.agents.schemas import Citation
from app.rag.store import get_collection, search_similar
from app.rag.retriever import build_retriever
from app.agents.ifrs import answer_ifrs


@dataclass
class ChecklistItem:
    """Individual checklist item for IFRS compliance."""
    
    id: str
    key: str
    description: str
    met: bool
    notes: Optional[str] = None
    citations: List[Citation] = field(default_factory=list)


@dataclass
class Feedback:
    """Structured feedback for document analysis."""
    
    status: str  # "OK", "NEEDS_REVIEW", "ABSTAIN"
    summary: str
    items: List[ChecklistItem]
    confidence: float


class DocumentFeedbackAnalyzer:
    """Analyzes documents against IFRS standards and provides structured feedback."""
    
    def __init__(self, checklist_file: Optional[str] = None):
        """Initialize analyzer with checklist configuration.
        
        Args:
            checklist_file: Path to checklist YAML file
        """
        if checklist_file is None:
            checklist_file = Path(__file__).parent.parent / "policy" / "ifrs13_checklist.yml"
        
        self.checklist_config = self._load_checklist(checklist_file)
        self.retriever = build_retriever(k=6, score_threshold=0.2)
    
    def _load_checklist(self, checklist_file: str) -> Dict[str, Any]:
        """Load checklist configuration from YAML file.
        
        Args:
            checklist_file: Path to checklist file
            
        Returns:
            Loaded checklist configuration
        """
        try:
            with open(checklist_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load checklist from {checklist_file}: {e}")
            return self._get_default_checklist()
    
    def _get_default_checklist(self) -> Dict[str, Any]:
        """Get default checklist configuration.
        
        Returns:
            Default checklist configuration
        """
        return {
            "checklist": {
                "items": [
                    {
                        "id": "hierarchy_defined",
                        "key": "hierarchy_defined",
                        "description": "Fair value hierarchy level is clearly defined",
                        "critical": True,
                        "category": "hierarchy"
                    }
                ],
                "critical_items": ["hierarchy_defined"]
            }
        }
    
    def analyze_document(self, doc_id: str, focus_standard: str = "IFRS 13") -> Feedback:
        """Analyze a document against IFRS standards.
        
        Args:
            doc_id: Document identifier
            focus_standard: IFRS standard to focus on (default: IFRS 13)
            
        Returns:
            Structured feedback with checklist items and citations
        """
        try:
            # Load document content from vector store
            document_content = self._load_document_content(doc_id)
            if not document_content:
                return self._create_abstain_feedback("Document not found or no content available")
            
            # Get checklist items
            checklist_items = self.checklist_config.get("checklist", {}).get("items", [])
            critical_items = self.checklist_config.get("checklist", {}).get("critical_items", [])
            
            # Analyze each checklist item
            analyzed_items = []
            total_confidence = 0.0
            critical_failures = 0
            
            for item_config in checklist_items:
                item_id = item_config.get("id", "")
                item_key = item_config.get("key", "")
                description = item_config.get("description", "")
                is_critical = item_id in critical_items
                
                # Create question for this checklist item
                question = self._create_checklist_question(description, focus_standard)
                
                # Get answer using IFRS agent
                answer = answer_ifrs(question, standard_filter=focus_standard)
                
                # Determine if item is met based on answer
                is_met, notes, citations = self._evaluate_checklist_item(answer, item_config)
                
                # Create checklist item
                checklist_item = ChecklistItem(
                    id=item_id,
                    key=item_key,
                    description=description,
                    met=is_met,
                    notes=notes,
                    citations=citations
                )
                
                analyzed_items.append(checklist_item)
                total_confidence += answer.confidence
                
                # Track critical failures
                if is_critical and not is_met:
                    critical_failures += 1
            
            # Calculate overall confidence
            avg_confidence = total_confidence / len(analyzed_items) if analyzed_items else 0.0
            
            # Determine status
            status = self._determine_status(critical_failures, avg_confidence)
            
            # Create summary
            summary = self._create_summary(analyzed_items, critical_failures, avg_confidence)
            
            return Feedback(
                status=status,
                summary=summary,
                items=analyzed_items,
                confidence=avg_confidence
            )
            
        except Exception as e:
            return self._create_abstain_feedback(f"Error analyzing document: {str(e)}")
    
    def _load_document_content(self, doc_id: str) -> Optional[str]:
        """Load document content from vector store.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Document content or None if not found
        """
        try:
            # Get collection directly
            from app.rag.store import get_vector_store
            client = get_vector_store()
            collection = get_collection(client, "ifrs_documents")
            
            # Find documents with matching doc_id
            doc_results = []
            for doc in collection.get("documents", []):
                metadata = doc.get("metadata", {})
                if metadata.get("doc_id") == doc_id:
                    doc_results.append(doc)
            
            if not doc_results:
                return None
            
            # Combine content from all chunks
            content_parts = []
            for result in doc_results:
                content = result.get("content", "")
                if content:
                    content_parts.append(content)
            
            return "\n\n".join(content_parts) if content_parts else None
            
        except Exception as e:
            print(f"Error loading document content: {e}")
            return None
    
    def _create_checklist_question(self, description: str, focus_standard: str) -> str:
        """Create a question for checklist item analysis.
        
        Args:
            description: Checklist item description
            focus_standard: IFRS standard to focus on
            
        Returns:
            Formatted question for analysis
        """
        return f"Does the document address the following {focus_standard} requirement: {description}? Please provide specific evidence and citations from the document."
    
    def _evaluate_checklist_item(self, answer, item_config: Dict[str, Any]) -> tuple[bool, Optional[str], List[Citation]]:
        """Evaluate a checklist item based on IFRS agent answer.
        
        Args:
            answer: IFRS agent answer
            item_config: Checklist item configuration
            
        Returns:
            Tuple of (is_met, notes, citations)
        """
        # Determine if item is met based on answer status and confidence
        is_met = answer.status == "OK" and answer.confidence >= 0.6
        
        # Create notes
        notes = None
        if answer.status == "ABSTAIN":
            notes = f"Unable to determine: {answer.answer}"
        elif answer.status == "OK":
            notes = f"Evidence found: {answer.answer[:200]}..."
        else:
            notes = f"Analysis result: {answer.answer}"
        
        # Extract citations
        citations = answer.citations if answer.citations else []
        
        return is_met, notes, citations
    
    def _determine_status(self, critical_failures: int, confidence: float) -> str:
        """Determine overall feedback status.
        
        Args:
            critical_failures: Number of critical items that failed
            confidence: Overall confidence score
            
        Returns:
            Status: "OK", "NEEDS_REVIEW", or "ABSTAIN"
        """
        if confidence < 0.65:
            return "ABSTAIN"
        elif critical_failures > 0:
            return "NEEDS_REVIEW"
        else:
            return "OK"
    
    def _create_summary(self, items: List[ChecklistItem], critical_failures: int, confidence: float) -> str:
        """Create summary of feedback analysis.
        
        Args:
            items: List of analyzed checklist items
            critical_failures: Number of critical failures
            confidence: Overall confidence score
            
        Returns:
            Summary text
        """
        total_items = len(items)
        met_items = sum(1 for item in items if item.met)
        met_percentage = (met_items / total_items * 100) if total_items > 0 else 0
        
        summary_parts = [
            f"Document analysis completed with {met_percentage:.1f}% compliance ({met_items}/{total_items} items met)."
        ]
        
        if critical_failures > 0:
            summary_parts.append(f"⚠️ {critical_failures} critical requirements not met.")
        
        if confidence < 0.65:
            summary_parts.append("⚠️ Low confidence in analysis - manual review recommended.")
        
        if met_percentage >= 80:
            summary_parts.append("✅ Document shows good IFRS 13 compliance.")
        elif met_percentage >= 60:
            summary_parts.append("⚠️ Document shows moderate IFRS 13 compliance - some improvements needed.")
        else:
            summary_parts.append("❌ Document shows poor IFRS 13 compliance - significant improvements needed.")
        
        return " ".join(summary_parts)
    
    def _create_abstain_feedback(self, reason: str) -> Feedback:
        """Create an ABSTAIN feedback response.
        
        Args:
            reason: Reason for abstaining
            
        Returns:
            ABSTAIN feedback
        """
        return Feedback(
            status="ABSTAIN",
            summary=f"Cannot analyze document: {reason}",
            items=[],
            confidence=0.0
        )


# Global analyzer instance
feedback_analyzer = DocumentFeedbackAnalyzer()


def analyze_document(doc_id: str, focus_standard: str = "IFRS 13") -> Feedback:
    """Analyze a document against IFRS standards.
    
    Args:
        doc_id: Document identifier
        focus_standard: IFRS standard to focus on
        
    Returns:
        Structured feedback with checklist items and citations
    """
    return feedback_analyzer.analyze_document(doc_id, focus_standard)
