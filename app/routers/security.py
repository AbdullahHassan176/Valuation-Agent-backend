"""
Security API endpoints for validation and backup management
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..security.validator import validate_security, SecurityReport
from ..security.backup import BackupManager, BackupInfo, RestoreResult

router = APIRouter(prefix="/security", tags=["security"])

# Request/Response models
class SecurityValidationRequest(BaseModel):
    """Request model for security validation"""
    config: Dict[str, Any]

class SecurityValidationResponse(BaseModel):
    """Response model for security validation"""
    timestamp: str
    overall_score: float
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    critical_issues: int
    checks: List[Dict[str, Any]]
    summary: Dict[str, Any]

class BackupRequest(BaseModel):
    """Request model for backup operations"""
    backup_type: str  # "full", "database", "vectors"
    description: Optional[str] = None

class BackupResponse(BaseModel):
    """Response model for backup operations"""
    backup_id: str
    timestamp: str
    size_bytes: int
    file_path: str
    checksum: str
    description: str
    backup_type: str

class RestoreRequest(BaseModel):
    """Request model for restore operations"""
    backup_id: str
    target_dir: Optional[str] = None

class RestoreResponse(BaseModel):
    """Response model for restore operations"""
    success: bool
    message: str
    restored_files: List[str]
    errors: List[str]

class BackupListResponse(BaseModel):
    """Response model for backup listing"""
    backups: List[Dict[str, Any]]
    total_count: int

# Dependency to get backup manager
def get_backup_manager() -> BackupManager:
    """Get backup manager instance"""
    return BackupManager()

@router.post("/validate", response_model=SecurityValidationResponse)
async def validate_security_config(request: SecurityValidationRequest):
    """
    Validate security configuration
    
    Performs comprehensive security validation including:
    - API security (rate limiting, request size limits)
    - CORS security (origin validation)
    - Data security (PII redaction, database security)
    - Environment security (debug mode, sensitive variables)
    - Network security (HTTPS enforcement)
    """
    try:
        # Perform security validation
        report = validate_security(request.config)
        
        # Convert to response format
        checks_data = []
        for check in report.checks:
            checks_data.append({
                "id": check.id,
                "name": check.name,
                "status": check.status.value,
                "level": check.level.value,
                "message": check.message,
                "details": check.details,
                "recommendations": check.recommendations
            })
        
        return SecurityValidationResponse(
            timestamp=report.timestamp.isoformat(),
            overall_score=report.overall_score,
            total_checks=report.total_checks,
            passed_checks=report.passed_checks,
            failed_checks=report.failed_checks,
            warning_checks=report.warning_checks,
            critical_issues=report.critical_issues,
            checks=checks_data,
            summary=report.summary
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Security validation failed: {str(e)}"
        )

@router.post("/backup", response_model=BackupResponse)
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    backup_manager: BackupManager = Depends(get_backup_manager)
):
    """
    Create a backup of application data
    
    Backup types:
    - full: Complete application backup
    - database: Database files only
    - vectors: Vector store data only
    """
    try:
        if request.backup_type == "full":
            backup_info = backup_manager.create_full_backup(request.description or "Full backup")
        elif request.backup_type == "database":
            backup_info = backup_manager.create_database_backup(request.description or "Database backup")
        elif request.backup_type == "vectors":
            backup_info = backup_manager.create_vectors_backup(request.description or "Vectors backup")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid backup type: {request.backup_type}. Valid types: full, database, vectors"
            )
        
        return BackupResponse(
            backup_id=backup_info.backup_id,
            timestamp=backup_info.timestamp.isoformat(),
            size_bytes=backup_info.size_bytes,
            file_path=backup_info.file_path,
            checksum=backup_info.checksum,
            description=backup_info.description,
            backup_type=backup_info.backup_type
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Backup creation failed: {str(e)}"
        )

@router.get("/backups", response_model=BackupListResponse)
async def list_backups(backup_manager: BackupManager = Depends(get_backup_manager)):
    """
    List all available backups
    """
    try:
        backups = backup_manager.list_backups()
        
        backups_data = []
        for backup in backups:
            backups_data.append({
                "backup_id": backup.backup_id,
                "timestamp": backup.timestamp.isoformat(),
                "size_bytes": backup.size_bytes,
                "file_path": backup.file_path,
                "checksum": backup.checksum,
                "description": backup.description,
                "backup_type": backup.backup_type
            })
        
        return BackupListResponse(
            backups=backups_data,
            total_count=len(backups_data)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list backups: {str(e)}"
        )

@router.post("/restore", response_model=RestoreResponse)
async def restore_backup(
    request: RestoreRequest,
    backup_manager: BackupManager = Depends(get_backup_manager)
):
    """
    Restore from a backup
    
    Specify the backup_id to restore from. Optionally specify a target directory.
    """
    try:
        result = backup_manager.restore_backup(request.backup_id, request.target_dir)
        
        return RestoreResponse(
            success=result.success,
            message=result.message,
            restored_files=result.restored_files,
            errors=result.errors
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Restore failed: {str(e)}"
        )

@router.delete("/backups/{backup_id}")
async def delete_backup(
    backup_id: str,
    backup_manager: BackupManager = Depends(get_backup_manager)
):
    """
    Delete a backup and its metadata
    """
    try:
        success = backup_manager.delete_backup(backup_id)
        
        if success:
            return {"message": f"Backup {backup_id} deleted successfully"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Backup {backup_id} not found"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete backup: {str(e)}"
        )

@router.post("/backups/cleanup")
async def cleanup_old_backups(
    days_to_keep: int = 30,
    backup_manager: BackupManager = Depends(get_backup_manager)
):
    """
    Clean up backups older than specified days
    """
    try:
        deleted_count = backup_manager.cleanup_old_backups(days_to_keep)
        
        return {
            "message": f"Cleaned up {deleted_count} old backups",
            "deleted_count": deleted_count,
            "days_to_keep": days_to_keep
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )

@router.get("/backups/{backup_id}/verify")
async def verify_backup(
    backup_id: str,
    backup_manager: BackupManager = Depends(get_backup_manager)
):
    """
    Verify backup integrity using checksum
    """
    try:
        backups = backup_manager.list_backups()
        backup = next((b for b in backups if b.backup_id == backup_id), None)
        
        if not backup:
            raise HTTPException(
                status_code=404,
                detail=f"Backup {backup_id} not found"
            )
        
        from pathlib import Path
        backup_path = Path(backup.file_path)
        
        if not backup_path.exists():
            return {
                "backup_id": backup_id,
                "exists": False,
                "message": "Backup file not found"
            }
        
        # Verify checksum
        from ..security.backup import BackupManager
        temp_manager = BackupManager()
        is_valid = temp_manager._verify_checksum(backup_path, backup.checksum)
        
        return {
            "backup_id": backup_id,
            "exists": True,
            "valid": is_valid,
            "checksum": backup.checksum,
            "size_bytes": backup.size_bytes,
            "message": "Backup is valid" if is_valid else "Backup checksum verification failed"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Backup verification failed: {str(e)}"
        )

@router.get("/status")
async def get_security_status():
    """
    Get current security system status
    """
    return {
        "status": "operational",
        "version": "1.0.0",
        "description": "Security validation and backup management system",
        "features": [
            "Security configuration validation",
            "Full application backup",
            "Database backup",
            "Vector store backup",
            "Backup integrity verification",
            "Automated cleanup"
        ],
        "timestamp": datetime.now().isoformat()
    }



