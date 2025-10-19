"""Prompt templates for IFRS agent."""

from typing import List, Dict, Any


def get_system_prompt() -> str:
    """Get the system prompt for IFRS assistant."""
    return """You are an expert IFRS assistant specializing in IFRS 9, IFRS 13, and IFRS 16 standards. 

Your role is to provide accurate, well-sourced answers about International Financial Reporting Standards using only the retrieved document sources provided to you.

IMPORTANT INSTRUCTIONS:
1. ONLY use information from the provided sources - do not use external knowledge
2. Always include proper citations with (standard, paragraph, section) format
3. Provide a confidence score between 0 and 1 based on source quality and completeness
4. If sources are insufficient, conflicting, or unclear, respond with status='ABSTAIN'
5. When abstaining, explain what additional information is needed
6. Structure your response as valid JSON with the required fields

RESPONSE FORMAT:
- status: "OK" for confident answers, "ABSTAIN" for insufficient information
- answer: Your response text or abstention reason
- citations: List of citations with standard, paragraph, and section
- confidence: Numeric score from 0.0 to 1.0

CITATION FORMAT:
- standard: "IFRS 9", "IFRS 13", "IFRS 16", etc.
- paragraph: Paragraph number or reference
- section: Section title if available

CONFIDENCE GUIDELINES:
- 0.9-1.0: Multiple clear, consistent sources
- 0.7-0.8: Single clear source or mostly consistent sources
- 0.5-0.6: Limited or somewhat unclear sources
- 0.0-0.4: Insufficient or conflicting sources (should ABSTAIN)

Always prioritize accuracy over completeness. When in doubt, abstain and ask for clarification."""


def format_retrieved_documents(documents: List[Dict[str, Any]]) -> str:
    """Format retrieved documents for the prompt.
    
    Args:
        documents: List of retrieved documents with metadata
        
    Returns:
        Formatted string of documents
    """
    if not documents:
        return "No relevant documents found."
    
    formatted_docs = []
    for i, doc in enumerate(documents, 1):
        content = doc.get("content", "")
        metadata = doc.get("metadata", {})
        score = doc.get("score", 0.0)
        
        # Extract metadata
        standard = metadata.get("standard", "Unknown")
        section = metadata.get("section", "Unknown")
        paragraph = metadata.get("paragraph", "Unknown")
        page_from = metadata.get("page_from", 0)
        page_to = metadata.get("page_to", 0)
        
        # Format document
        doc_text = f"""Document {i} (Relevance: {score:.2f}):
Standard: {standard}
Section: {section}
Paragraph: {paragraph}
Pages: {page_from}-{page_to}
Content: {content[:500]}{'...' if len(content) > 500 else ''}"""
        
        formatted_docs.append(doc_text)
    
    return "\n\n".join(formatted_docs)


def create_question_prompt(question: str, documents: List[Dict[str, Any]]) -> str:
    """Create the complete prompt for IFRS question answering.
    
    Args:
        question: User's question
        documents: Retrieved documents
        
    Returns:
        Complete prompt for the LLM
    """
    system_prompt = get_system_prompt()
    formatted_docs = format_retrieved_documents(documents)
    
    prompt = f"""{system_prompt}

RETRIEVED SOURCES:
{formatted_docs}

USER QUESTION: {question}

Please provide a structured JSON response with the following format:
{{
    "status": "OK" or "ABSTAIN",
    "answer": "Your detailed response or abstention reason",
    "citations": [
        {{
            "standard": "IFRS 9",
            "paragraph": "4.1.1",
            "section": "Recognition and Measurement"
        }}
    ],
    "confidence": 0.85
}}

Remember: Only use information from the provided sources. If the sources don't contain sufficient information to answer the question confidently, set status to "ABSTAIN" and explain what additional information would be needed."""
    
    return prompt


def get_abstain_prompt(question: str, reason: str = "insufficient sources") -> str:
    """Get a prompt for abstaining when no sources are available.
    
    Args:
        question: User's question
        reason: Reason for abstaining
        
    Returns:
        Abstain response
    """
    return f"""Question: {question}

I cannot answer this question because {reason}. 

To provide an accurate answer, I would need access to relevant IFRS documentation that covers this topic. Please ensure that the appropriate IFRS standards (IFRS 9, IFRS 13, or IFRS 16) have been uploaded and processed in the system.

If you have specific IFRS documents that should contain this information, please upload them and try again."""
