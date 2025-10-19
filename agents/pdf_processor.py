"""
PDF processing utilities for extracting text from uploaded PDFs.
"""

import io
from typing import Optional
import PyPDF2


class PDFProcessor:
    """Handles PDF text extraction using multiple methods."""
    
    @staticmethod
    def extract_text_from_pdf(pdf_content: bytes) -> str:
        """
        Extract text from PDF content using PyPDF2.
        
        Args:
            pdf_content: Raw PDF file content as bytes
            
        Returns:
            Extracted text string
        """
        text = ""
        
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            print(f"PyPDF2 failed: {e}")
        
        return text.strip()
    
    @staticmethod
    def validate_pdf(pdf_content: bytes) -> tuple[bool, Optional[str]]:
        """
        Validate that the uploaded file is a valid PDF.
        
        Args:
            pdf_content: Raw PDF file content as bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not pdf_content:
            return False, "No file content provided"
        
        if len(pdf_content) < 100:
            return False, "File too small to be a valid PDF"
        
        # Check PDF header
        if not pdf_content.startswith(b'%PDF-'):
            return False, "File does not appear to be a valid PDF"
        
        # Try to read the PDF
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            if len(pdf_reader.pages) == 0:
                return False, "PDF has no pages"
        except Exception as e:
            return False, f"Invalid PDF format: {str(e)}"
        
        return True, None
