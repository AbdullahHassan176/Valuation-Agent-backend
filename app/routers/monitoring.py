"""
Performance monitoring API endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from ..monitoring.metrics import performance_monitor, Alert, AlertLevel, AlertEvent

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Request/Response models
class PerformanceSummaryResponse(BaseModel):
    """Response model for performance summary"""
    timestamp: str
    system: Dict[str, Any]
    requests: Dict[str, Any]
    alerts: Dict[str, Any]

class AlertRequest(BaseModel):
    """Request model for creating alerts"""
    id: str
    name: str
    condition: str
    threshold: float
    level: str
    enabled: bool = True
    cooldown_minutes: int = 5

class AlertResponse(BaseModel):
    """Response model for alert operations"""
    id: str
    name: str
    condition: str
    threshold: float
    level: str
    enabled: bool
    cooldown_minutes: int

class AlertEventResponse(BaseModel):
    """Response model for alert events"""
    alert_id: str
    alert_name: str
    current_value: float
    threshold: float
    level: str
    timestamp: str
    message: str

class MetricHistoryRequest(BaseModel):
    """Request model for metric history"""
    metric_name: str
    minutes: int = 60

class MetricHistoryResponse(BaseModel):
    """Response model for metric history"""
    metric_name: str
    data_points: List[Dict[str, Any]]
    summary: Dict[str, Any]

@router.get("/summary", response_model=PerformanceSummaryResponse)
async def get_performance_summary():
    """
    Get comprehensive performance summary
    
    Returns system metrics, request statistics, and alert information
    """
    try:
        summary = performance_monitor.get_performance_summary()
        return PerformanceSummaryResponse(**summary)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance summary: {str(e)}"
        )

@router.get("/metrics/{metric_name}")
async def get_metric_data(
    metric_name: str,
    minutes: int = 60
):
    """
    Get metric data for a specific metric
    
    Returns historical data and summary statistics
    """
    try:
        # Get metric history
        history = performance_monitor.metrics.get_metric_history(metric_name, minutes)
        data_points = [
            {
                "timestamp": metric.timestamp.isoformat(),
                "value": metric.value,
                "tags": metric.tags
            }
            for metric in history
        ]
        
        # Get summary statistics
        summary = performance_monitor.metrics.get_metric_summary(metric_name, minutes)
        
        return {
            "metric_name": metric_name,
            "data_points": data_points,
            "summary": summary,
            "time_range_minutes": minutes
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metric data: {str(e)}"
        )

@router.get("/metrics/{metric_name}/stats")
async def get_metric_stats(metric_name: str):
    """
    Get statistical summary for a metric
    
    Returns count, average, min, max, and percentiles
    """
    try:
        if "timer" in metric_name or "duration" in metric_name:
            stats = performance_monitor.metrics.get_timer_stats(metric_name)
        else:
            stats = performance_monitor.metrics.get_metric_summary(metric_name, minutes=60)
        
        return {
            "metric_name": metric_name,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metric stats: {str(e)}"
        )

@router.post("/alerts", response_model=AlertResponse)
async def create_alert(request: AlertRequest):
    """
    Create a new alert
    
    Define alert conditions and thresholds for monitoring
    """
    try:
        # Validate alert level
        try:
            alert_level = AlertLevel(request.level)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid alert level: {request.level}. Valid levels: info, warning, critical"
            )
        
        # Create alert
        alert = Alert(
            id=request.id,
            name=request.name,
            condition=request.condition,
            threshold=request.threshold,
            level=alert_level,
            enabled=request.enabled,
            cooldown_minutes=request.cooldown_minutes
        )
        
        # Add to alert manager
        performance_monitor.alert_manager.add_alert(alert)
        
        return AlertResponse(
            id=alert.id,
            name=alert.name,
            condition=alert.condition,
            threshold=alert.threshold,
            level=alert.level.value,
            enabled=alert.enabled,
            cooldown_minutes=alert.cooldown_minutes
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create alert: {str(e)}"
        )

@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts():
    """
    List all configured alerts
    """
    try:
        alerts = []
        for alert in performance_monitor.alert_manager.alerts.values():
            alerts.append(AlertResponse(
                id=alert.id,
                name=alert.name,
                condition=alert.condition,
                threshold=alert.threshold,
                level=alert.level.value,
                enabled=alert.enabled,
                cooldown_minutes=alert.cooldown_minutes
            ))
        
        return alerts
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list alerts: {str(e)}"
        )

@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """
    Delete an alert
    """
    try:
        performance_monitor.alert_manager.remove_alert(alert_id)
        return {"message": f"Alert {alert_id} deleted successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete alert: {str(e)}"
        )

@router.post("/alerts/check")
async def check_alerts():
    """
    Manually check all alerts and return triggered events
    """
    try:
        triggered_events = performance_monitor.check_alerts()
        
        events = []
        for event in triggered_events:
            events.append(AlertEventResponse(
                alert_id=event.alert_id,
                alert_name=event.alert_name,
                current_value=event.current_value,
                threshold=event.threshold,
                level=event.level.value,
                timestamp=event.timestamp.isoformat(),
                message=event.message
            ))
        
        return {
            "triggered_events": events,
            "count": len(events),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check alerts: {str(e)}"
        )

@router.get("/alerts/events", response_model=List[AlertEventResponse])
async def get_alert_events(hours: int = 24):
    """
    Get alert events from the last N hours
    """
    try:
        events = performance_monitor.alert_manager.get_alert_events(hours)
        
        event_responses = []
        for event in events:
            event_responses.append(AlertEventResponse(
                alert_id=event.alert_id,
                alert_name=event.alert_name,
                current_value=event.current_value,
                threshold=event.threshold,
                level=event.level.value,
                timestamp=event.timestamp.isoformat(),
                message=event.message
            ))
        
        return event_responses
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alert events: {str(e)}"
        )

@router.get("/system/health")
async def get_system_health():
    """
    Get system health status
    """
    try:
        import psutil
        
        # Get current system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Determine health status
        health_status = "healthy"
        issues = []
        
        if cpu_percent > 90:
            health_status = "critical"
            issues.append(f"CPU usage is {cpu_percent:.1f}%")
        elif cpu_percent > 80:
            health_status = "warning"
            issues.append(f"CPU usage is {cpu_percent:.1f}%")
        
        if memory.percent > 95:
            health_status = "critical"
            issues.append(f"Memory usage is {memory.percent:.1f}%")
        elif memory.percent > 85:
            health_status = "warning"
            issues.append(f"Memory usage is {memory.percent:.1f}%")
        
        if disk.percent > 95:
            health_status = "critical"
            issues.append(f"Disk usage is {disk.percent:.1f}%")
        elif disk.percent > 90:
            health_status = "warning"
            issues.append(f"Disk usage is {disk.percent:.1f}%")
        
        return {
            "status": health_status,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_free_gb": disk.free / (1024**3)
            },
            "issues": issues
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system health: {str(e)}"
        )

@router.post("/metrics/record")
async def record_custom_metric(
    name: str,
    value: float,
    tags: Optional[Dict[str, str]] = None
):
    """
    Record a custom metric
    """
    try:
        performance_monitor.metrics.record_metric(name, value, tags or {})
        return {"message": f"Metric {name} recorded successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record metric: {str(e)}"
        )

@router.get("/status")
async def get_monitoring_status():
    """
    Get monitoring system status
    """
    return {
        "status": "operational",
        "version": "1.0.0",
        "description": "Performance monitoring and alerting system",
        "features": [
            "System metrics collection",
            "Request performance tracking",
            "Custom metrics recording",
            "Alert management",
            "Health monitoring"
        ],
        "timestamp": datetime.now().isoformat()
    }
