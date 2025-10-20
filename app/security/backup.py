"""
Backup and restore system for the Valuation Agent platform
"""
import os
import json
import shutil
import tarfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import hashlib
import sqlite3

@dataclass
class BackupInfo:
    """Backup information"""
    backup_id: str
    timestamp: datetime
    size_bytes: int
    file_path: str
    checksum: str
    description: str
    backup_type: str  # "full", "incremental", "database", "vectors"

@dataclass
class RestoreResult:
    """Restore operation result"""
    success: bool
    message: str
    restored_files: List[str]
    errors: List[str]

class BackupManager:
    """Backup and restore management system"""
    
    def __init__(self, backup_dir: str = "./backups", data_dir: str = "./data"):
        self.backup_dir = Path(backup_dir)
        self.data_dir = Path(data_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_full_backup(self, description: str = "Full backup") -> BackupInfo:
        """Create a full backup of all application data"""
        timestamp = datetime.now()
        backup_id = f"backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / f"{backup_id}.tar.gz"
        
        # Create tar.gz backup
        with tarfile.open(backup_path, "w:gz") as tar:
            # Add data directory
            if self.data_dir.exists():
                tar.add(self.data_dir, arcname="data")
            
            # Add configuration files
            config_files = [".env", "docker-compose.yml", "docker-compose.dev.yml", "docker-compose.prod.yml"]
            for config_file in config_files:
                if Path(config_file).exists():
                    tar.add(config_file, arcname=config_file)
        
        # Calculate checksum
        checksum = self._calculate_checksum(backup_path)
        size_bytes = backup_path.stat().st_size
        
        # Create backup info
        backup_info = BackupInfo(
            backup_id=backup_id,
            timestamp=timestamp,
            size_bytes=size_bytes,
            file_path=str(backup_path),
            checksum=checksum,
            description=description,
            backup_type="full"
        )
        
        # Save backup metadata
        self._save_backup_metadata(backup_info)
        
        return backup_info
    
    def create_database_backup(self, description: str = "Database backup") -> BackupInfo:
        """Create a backup of the database only"""
        timestamp = datetime.now()
        backup_id = f"db_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / f"{backup_id}.db"
        
        # Find database files
        db_files = []
        for db_file in self.data_dir.rglob("*.db"):
            db_files.append(db_file)
        
        if not db_files:
            raise ValueError("No database files found to backup")
        
        # Copy database files
        for db_file in db_files:
            shutil.copy2(db_file, backup_path)
        
        # Calculate checksum
        checksum = self._calculate_checksum(backup_path)
        size_bytes = backup_path.stat().st_size
        
        # Create backup info
        backup_info = BackupInfo(
            backup_id=backup_id,
            timestamp=timestamp,
            size_bytes=size_bytes,
            file_path=str(backup_path),
            checksum=checksum,
            description=description,
            backup_type="database"
        )
        
        # Save backup metadata
        self._save_backup_metadata(backup_info)
        
        return backup_info
    
    def create_vectors_backup(self, description: str = "Vectors backup") -> BackupInfo:
        """Create a backup of vector store data"""
        timestamp = datetime.now()
        backup_id = f"vectors_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / f"{backup_id}.tar.gz"
        
        vectors_dir = self.data_dir / "vectors"
        if not vectors_dir.exists():
            raise ValueError("Vectors directory not found")
        
        # Create tar.gz backup of vectors
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(vectors_dir, arcname="vectors")
        
        # Calculate checksum
        checksum = self._calculate_checksum(backup_path)
        size_bytes = backup_path.stat().st_size
        
        # Create backup info
        backup_info = BackupInfo(
            backup_id=backup_id,
            timestamp=timestamp,
            size_bytes=size_bytes,
            file_path=str(backup_path),
            checksum=checksum,
            description=description,
            backup_type="vectors"
        )
        
        # Save backup metadata
        self._save_backup_metadata(backup_info)
        
        return backup_info
    
    def restore_backup(self, backup_id: str, target_dir: Optional[str] = None) -> RestoreResult:
        """Restore from a backup"""
        try:
            # Load backup metadata
            backup_info = self._load_backup_metadata(backup_id)
            if not backup_info:
                return RestoreResult(
                    success=False,
                    message=f"Backup {backup_id} not found",
                    restored_files=[],
                    errors=[f"Backup {backup_id} not found"]
                )
            
            backup_path = Path(backup_info.file_path)
            if not backup_path.exists():
                return RestoreResult(
                    success=False,
                    message=f"Backup file not found: {backup_path}",
                    restored_files=[],
                    errors=[f"Backup file not found: {backup_path}"]
                )
            
            # Verify checksum
            if not self._verify_checksum(backup_path, backup_info.checksum):
                return RestoreResult(
                    success=False,
                    message="Backup file checksum verification failed",
                    restored_files=[],
                    errors=["Checksum verification failed"]
                )
            
            # Determine target directory
            if target_dir:
                restore_dir = Path(target_dir)
            else:
                restore_dir = self.data_dir
            
            restore_dir.mkdir(parents=True, exist_ok=True)
            
            restored_files = []
            errors = []
            
            # Restore based on backup type
            if backup_info.backup_type == "full":
                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.extractall(restore_dir)
                    restored_files = tar.getnames()
            
            elif backup_info.backup_type == "database":
                # Restore database files
                if backup_path.suffix == ".db":
                    target_db = restore_dir / "audit.db"
                    shutil.copy2(backup_path, target_db)
                    restored_files = [str(target_db)]
                else:
                    with tarfile.open(backup_path, "r:gz") as tar:
                        tar.extractall(restore_dir)
                        restored_files = tar.getnames()
            
            elif backup_info.backup_type == "vectors":
                vectors_dir = restore_dir / "vectors"
                vectors_dir.mkdir(parents=True, exist_ok=True)
                
                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.extractall(restore_dir)
                    restored_files = tar.getnames()
            
            return RestoreResult(
                success=True,
                message=f"Successfully restored backup {backup_id}",
                restored_files=restored_files,
                errors=errors
            )
            
        except Exception as e:
            return RestoreResult(
                success=False,
                message=f"Restore failed: {str(e)}",
                restored_files=[],
                errors=[str(e)]
            )
    
    def list_backups(self) -> List[BackupInfo]:
        """List all available backups"""
        backups = []
        
        # Load metadata files
        for metadata_file in self.backup_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    backup_info = BackupInfo(
                        backup_id=metadata['backup_id'],
                        timestamp=datetime.fromisoformat(metadata['timestamp']),
                        size_bytes=metadata['size_bytes'],
                        file_path=metadata['file_path'],
                        checksum=metadata['checksum'],
                        description=metadata['description'],
                        backup_type=metadata['backup_type']
                    )
                    backups.append(backup_info)
            except Exception as e:
                print(f"Error loading backup metadata {metadata_file}: {e}")
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        
        return backups
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup and its metadata"""
        try:
            # Load backup metadata
            backup_info = self._load_backup_metadata(backup_id)
            if not backup_info:
                return False
            
            # Delete backup file
            backup_path = Path(backup_info.file_path)
            if backup_path.exists():
                backup_path.unlink()
            
            # Delete metadata file
            metadata_path = self.backup_dir / f"{backup_id}.json"
            if metadata_path.exists():
                metadata_path.unlink()
            
            return True
            
        except Exception as e:
            print(f"Error deleting backup {backup_id}: {e}")
            return False
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """Clean up backups older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        backups = self.list_backups()
        for backup in backups:
            if backup.timestamp < cutoff_date:
                if self.delete_backup(backup.backup_id):
                    deleted_count += 1
        
        return deleted_count
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Verify file checksum"""
        actual_checksum = self._calculate_checksum(file_path)
        return actual_checksum == expected_checksum
    
    def _save_backup_metadata(self, backup_info: BackupInfo):
        """Save backup metadata to JSON file"""
        metadata = {
            'backup_id': backup_info.backup_id,
            'timestamp': backup_info.timestamp.isoformat(),
            'size_bytes': backup_info.size_bytes,
            'file_path': backup_info.file_path,
            'checksum': backup_info.checksum,
            'description': backup_info.description,
            'backup_type': backup_info.backup_type
        }
        
        metadata_path = self.backup_dir / f"{backup_info.backup_id}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _load_backup_metadata(self, backup_id: str) -> Optional[BackupInfo]:
        """Load backup metadata from JSON file"""
        metadata_path = self.backup_dir / f"{backup_id}.json"
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                return BackupInfo(
                    backup_id=metadata['backup_id'],
                    timestamp=datetime.fromisoformat(metadata['timestamp']),
                    size_bytes=metadata['size_bytes'],
                    file_path=metadata['file_path'],
                    checksum=metadata['checksum'],
                    description=metadata['description'],
                    backup_type=metadata['backup_type']
                )
        except Exception as e:
            print(f"Error loading backup metadata: {e}")
            return None

def create_backup_manager(backup_dir: str = "./backups", data_dir: str = "./data") -> BackupManager:
    """Create a backup manager instance"""
    return BackupManager(backup_dir, data_dir)



