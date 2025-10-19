"""Document loading and parsing utilities."""

import os
from pathlib import Path
from typing import List, Optional
from app.models.documents import Page


def parse_file(file_path: str) -> List[Page]:
    """Parse a document file and extract text content.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        List of Page objects with extracted text
        
    Raises:
        ValueError: If file type is not supported
        FileNotFoundError: If file doesn't exist
        Exception: If parsing fails
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Get file extension
    file_ext = file_path.suffix.lower()
    
    try:
        if file_ext == '.txt':
            return _parse_txt(file_path)
        else:
            # For now, only support text files
            raise ValueError(f"File type {file_ext} not supported yet. Only .txt files are supported.")
    
    except Exception as e:
        raise Exception(f"Error parsing file {file_path}: {e}")


def _parse_txt(file_path: Path) -> List[Page]:
    """Parse text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content into pages (simple approach: split by double newlines)
        pages_content = content.split('\n\n')
        
        pages = []
        for i, page_content in enumerate(pages_content, 1):
            if page_content.strip():
                pages.append(Page(
                    page_number=i,
                    content=page_content.strip(),
                    metadata={'source': 'txt', 'file_type': file_path.suffix}
                ))
        
        # If no pages were created, create a single page with all content
        if not pages and content.strip():
            pages.append(Page(
                page_number=1,
                content=content.strip(),
                metadata={'source': 'txt', 'file_type': file_path.suffix}
            ))
        
        return pages
    
    except Exception as e:
        raise Exception(f"Error parsing text file {file_path}: {e}")
