"""File hashing utilities."""

import hashlib
from pathlib import Path


def file_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA256 hash as hexadecimal string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise IOError(f"Path is not a file: {file_path}")
    
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def string_sha256(content: str) -> str:
    """Calculate SHA256 hash of a string.
    
    Args:
        content: String content to hash
        
    Returns:
        SHA256 hash as hexadecimal string
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
