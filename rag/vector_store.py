"""
Local vector store implementation using simple in-memory storage for document retrieval
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import hashlib
import re
from collections import defaultdict


@dataclass
class Document:
    """Document with metadata for vector store"""
    id: str
    content: str
    metadata: Dict[str, Any]
    doc_name: str
    section_id: str
    paragraph_id: str


class VectorStore:
    """Local vector store for document retrieval using simple text matching"""
    
    def __init__(self, persist_directory: str = "backend/rag/simple_db"):
        """Initialize vector store with persistent storage"""
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Simple in-memory storage
        self.documents = {}
        self.documents_by_name = defaultdict(list)
        self.load_from_disk()
    
    def add_document(self, document: Document) -> str:
        """Add a document to the vector store"""
        # Generate unique ID if not provided
        if not document.id:
            content_hash = hashlib.md5(document.content.encode()).hexdigest()[:8]
            document.id = f"{document.doc_name}_{document.section_id}_{content_hash}"
        
        # Store document
        self.documents[document.id] = {
            "content": document.content,
            "metadata": document.metadata,
            "doc_name": document.doc_name,
            "section_id": document.section_id,
            "paragraph_id": document.paragraph_id
        }
        
        # Index by document name
        self.documents_by_name[document.doc_name].append(document.id)
        
        # Save to disk
        self.save_to_disk()
        
        return document.id
    
    def search_documents(
        self, 
        query: str, 
        n_results: int = 5,
        doc_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant documents using simple text matching"""
        
        # Get documents to search
        if doc_filter:
            doc_ids = self.documents_by_name.get(doc_filter, [])
        else:
            doc_ids = list(self.documents.keys())
        
        # Simple text matching
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        results = []
        
        for doc_id in doc_ids:
            doc = self.documents[doc_id]
            content_words = set(re.findall(r'\b\w+\b', doc["content"].lower()))
            
            # Calculate simple similarity
            common_words = query_words.intersection(content_words)
            similarity = len(common_words) / max(len(query_words), 1) if query_words else 0
            
            # Boost score for exact phrase matches
            if query.lower() in doc["content"].lower():
                similarity += 0.3
            
            results.append({
                "content": doc["content"],
                "metadata": {
                    **doc["metadata"],
                    "doc_name": doc["doc_name"],
                    "section_id": doc["section_id"],
                    "paragraph_id": doc["paragraph_id"]
                },
                "similarity_score": min(1.0, similarity),
                "rank": 0  # Will be set after sorting
            })
        
        # Sort by similarity and take top results
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        results = results[:n_results]
        
        # Set ranks
        for i, result in enumerate(results):
            result["rank"] = i + 1
        
        return results
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID"""
        if doc_id in self.documents:
            doc = self.documents[doc_id]
            return {
                "content": doc["content"],
                "metadata": doc["metadata"],
                "id": doc_id
            }
        return None
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents in the collection"""
        documents = []
        for doc_id, doc in self.documents.items():
            documents.append({
                "id": doc_id,
                "content": doc["content"],
                "metadata": doc["metadata"]
            })
        return documents
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the collection"""
        if doc_id in self.documents:
            doc = self.documents[doc_id]
            doc_name = doc["doc_name"]
            
            # Remove from documents
            del self.documents[doc_id]
            
            # Remove from name index
            if doc_id in self.documents_by_name[doc_name]:
                self.documents_by_name[doc_name].remove(doc_id)
            
            # Save to disk
            self.save_to_disk()
            return True
        return False
    
    def reset_collection(self) -> bool:
        """Reset the entire collection"""
        self.documents = {}
        self.documents_by_name = defaultdict(list)
        self.save_to_disk()
        return True
    
    def save_to_disk(self):
        """Save documents to disk"""
        try:
            data = {
                "documents": self.documents,
                "documents_by_name": dict(self.documents_by_name)
            }
            with open(os.path.join(self.persist_directory, "documents.json"), "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass  # Ignore save errors
    
    def load_from_disk(self):
        """Load documents from disk"""
        try:
            file_path = os.path.join(self.persist_directory, "documents.json")
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    data = json.load(f)
                    self.documents = data.get("documents", {})
                    self.documents_by_name = defaultdict(list, data.get("documents_by_name", {}))
        except Exception:
            pass  # Ignore load errors


class DocumentProcessor:
    """Process and prepare documents for vector store"""
    
    @staticmethod
    def create_sample_documents() -> List[Document]:
        """Create sample valuation methodology documents"""
        documents = []
        
        # IRS Valuation Methodology
        documents.append(Document(
            id="irs_methodology_1",
            content="Interest Rate Swap (IRS) valuation follows the discounted cash flow (DCF) methodology. The present value is calculated by discounting all future cash flows using the appropriate discount curve. For fixed legs, cash flows are determined by the fixed rate and day count convention. For floating legs, cash flows are projected using forward rates from the yield curve.",
            metadata={
                "content_type": "methodology",
                "source": "internal_policy",
                "version": "1.0"
            },
            doc_name="IRS_Valuation_Methodology",
            section_id="section_1",
            paragraph_id="para_1_1"
        ))
        
        documents.append(Document(
            id="irs_methodology_2",
            content="Day count conventions are critical for accurate accrual calculations. ACT/360 is the standard for USD swaps, while ACT/365 is used for EUR swaps. The Modified Following business day convention is applied to adjust payment dates that fall on weekends or holidays.",
            metadata={
                "content_type": "methodology",
                "source": "internal_policy",
                "version": "1.0"
            },
            doc_name="IRS_Valuation_Methodology",
            section_id="section_1",
            paragraph_id="para_1_2"
        ))
        
        # XVA Methodology
        documents.append(Document(
            id="xva_methodology_1",
            content="Credit Value Adjustment (CVA) represents the cost of counterparty credit risk. It is calculated as the expected loss from counterparty default, discounted to present value. CVA = (1 - Recovery Rate) × Σ[Expected Exposure(t) × Probability of Default(t) × Discount Factor(t)].",
            metadata={
                "content_type": "methodology",
                "source": "internal_policy",
                "version": "1.0"
            },
            doc_name="XVA_Methodology",
            section_id="section_2",
            paragraph_id="para_2_1"
        ))
        
        documents.append(Document(
            id="xva_methodology_2",
            content="Debit Value Adjustment (DVA) represents the benefit from our own credit risk. It is calculated similarly to CVA but using our own credit curve and negative exposures. DVA = (1 - Recovery Rate) × Σ[Expected Negative Exposure(t) × Our Probability of Default(t) × Discount Factor(t)].",
            metadata={
                "content_type": "methodology",
                "source": "internal_policy",
                "version": "1.0"
            },
            doc_name="XVA_Methodology",
            section_id="section_2",
            paragraph_id="para_2_2"
        ))
        
        documents.append(Document(
            id="xva_methodology_3",
            content="Funding Value Adjustment (FVA) represents the cost of funding risk. It is calculated as the expected funding cost over the life of the trade. FVA = Σ[Expected Exposure(t) × Funding Spread(t) × Discount Factor(t)]. CSA agreements can reduce FVA by providing collateral benefits.",
            metadata={
                "content_type": "methodology",
                "source": "internal_policy",
                "version": "1.0"
            },
            doc_name="XVA_Methodology",
            section_id="section_2",
            paragraph_id="para_2_3"
        ))
        
        # Risk Management Policy
        documents.append(Document(
            id="risk_policy_1",
            content="Sensitivity analysis is required for all valuation runs. Parallel curve bumps of ±1bp must be calculated to assess interest rate risk. The results should show reasonable symmetry and sign consistency. PV01 (Present Value of 1 basis point) should be calculated and validated against market expectations.",
            metadata={
                "content_type": "policy",
                "source": "internal_policy",
                "version": "1.0"
            },
            doc_name="Risk_Management_Policy",
            section_id="section_3",
            paragraph_id="para_3_1"
        ))
        
        documents.append(Document(
            id="risk_policy_2",
            content="Curve twist analysis is required for trades with maturities greater than 5 years. Short-end and long-end bumps should be applied separately to assess curve risk. Typical twist scenarios include steepening (+1bp long, -1bp short) and flattening (-1bp long, +1bp short).",
            metadata={
                "content_type": "policy",
                "source": "internal_policy",
                "version": "1.0"
            },
            doc_name="Risk_Management_Policy",
            section_id="section_3",
            paragraph_id="para_3_2"
        ))
        
        # IFRS-13 Compliance
        documents.append(Document(
            id="ifrs13_policy_1",
            content="IFRS-13 requires fair value hierarchy classification. Level 1 inputs are quoted prices in active markets. Level 2 inputs are observable market data other than quoted prices. Level 3 inputs are unobservable inputs requiring significant judgment. All valuation runs must be classified according to this hierarchy.",
            metadata={
                "content_type": "policy",
                "source": "internal_policy",
                "version": "1.0"
            },
            doc_name="IFRS13_Compliance_Policy",
            section_id="section_4",
            paragraph_id="para_4_1"
        ))
        
        documents.append(Document(
            id="ifrs13_policy_2",
            content="Day-1 P&L checks are required for all new trades. The initial profit or loss must be within acceptable tolerance of market quotes. If the Day-1 P&L exceeds tolerance, the trade must be flagged for review and require additional justification. This ensures proper fair value measurement at inception.",
            metadata={
                "content_type": "policy",
                "source": "internal_policy",
                "version": "1.0"
            },
            doc_name="IFRS13_Compliance_Policy",
            section_id="section_4",
            paragraph_id="para_4_2"
        ))
        
        # Excel Export Policy
        documents.append(Document(
            id="excel_policy_1",
            content="All valuation results must be exported to Excel with the following mandatory sheets: Cover, Instrument_Summary, Data_Sources, Curves, Cashflows, Results, Sensitivities, IFRS13_Assessment, Assumptions_Judgements, and Audit_Log. Each sheet must contain relevant data with proper lineage tracking.",
            metadata={
                "content_type": "policy",
                "source": "internal_policy",
                "version": "1.0"
            },
            doc_name="Excel_Export_Policy",
            section_id="section_5",
            paragraph_id="para_5_1"
        ))
        
        return documents
    
    @staticmethod
    def load_documents_from_directory(directory_path: str) -> List[Document]:
        """Load documents from a directory (placeholder for future PDF processing)"""
        # This would be implemented to process actual PDF files
        # For now, return empty list
        return []