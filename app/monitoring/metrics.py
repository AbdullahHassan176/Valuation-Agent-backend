"""
Performance monitoring and metrics collection system
"""
import time
import psutil
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import threading
from enum import Enum

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE

@dataclass
class Alert:
    """Alert definition"""
    id: str
    name: str
    condition: str
    threshold: float
    level: AlertLevel
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    cooldown_minutes: int = 5

@dataclass
class AlertEvent:
    """Alert event when threshold is exceeded"""
    alert_id: str
    alert_name: str
    current_value: float
    threshold: float
    level: AlertLevel
    timestamp: datetime
    message: str

class MetricsCollector:
    """Metrics collection and storage system"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, float] = defaultdict(float)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None, metric_type: MetricType = MetricType.GAUGE):
        """Record a metric value"""
        with self.lock:
            metric = Metric(
                name=name,
                value=value,
                timestamp=datetime.now(),
                tags=tags or {},
                metric_type=metric_type
            )
            self.metrics[name].append(metric)
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            self.counters[name] += value
            self.record_metric(name, self.counters[name], tags, MetricType.COUNTER)
    
    def record_timer(self, name: str, duration: float, tags: Dict[str, str] = None):
        """Record a timer metric"""
        with self.lock:
            self.timers[name].append(duration)
            # Keep only last 100 timer values
            if len(self.timers[name]) > 100:
                self.timers[name] = self.timers[name][-100:]
            self.record_metric(name, duration, tags, MetricType.TIMER)
    
    def get_metric_history(self, name: str, minutes: int = 60) -> List[Metric]:
        """Get metric history for the last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        with self.lock:
            return [m for m in self.metrics[name] if m.timestamp >= cutoff]
    
    def get_metric_summary(self, name: str, minutes: int = 60) -> Dict[str, Any]:
        """Get metric summary statistics"""
        history = self.get_metric_history(name, minutes)
        if not history:
            return {"count": 0, "avg": 0, "min": 0, "max": 0, "latest": 0}
        
        values = [m.value for m in history]
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1] if values else 0
        }
    
    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """Get timer statistics"""
        with self.lock:
            if not self.timers[name]:
                return {"count": 0, "avg": 0, "min": 0, "max": 0, "p95": 0, "p99": 0}
            
            values = sorted(self.timers[name])
            count = len(values)
            avg = sum(values) / count
            min_val = min(values)
            max_val = max(values)
            p95 = values[int(count * 0.95)] if count > 0 else 0
            p99 = values[int(count * 0.99)] if count > 0 else 0
            
            return {
                "count": count,
                "avg": avg,
                "min": min_val,
                "max": max_val,
                "p95": p95,
                "p99": p99
            }

class SystemMetricsCollector:
    """System-level metrics collection"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.running = False
        self.collection_task = None
    
    async def start_collection(self, interval: int = 30):
        """Start system metrics collection"""
        self.running = True
        self.collection_task = asyncio.create_task(self._collect_loop(interval))
    
    async def stop_collection(self):
        """Stop system metrics collection"""
        self.running = False
        if self.collection_task:
            self.collection_task.cancel()
    
    async def _collect_loop(self, interval: int):
        """Main collection loop"""
        while self.running:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error collecting system metrics: {e}")
                await asyncio.sleep(interval)
    
    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics.record_metric("system.cpu.usage", cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.metrics.record_metric("system.memory.usage", memory.percent)
        self.metrics.record_metric("system.memory.available", memory.available)
        self.metrics.record_metric("system.memory.used", memory.used)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        self.metrics.record_metric("system.disk.usage", disk.percent)
        self.metrics.record_metric("system.disk.free", disk.free)
        
        # Network I/O
        net_io = psutil.net_io_counters()
        self.metrics.record_metric("system.network.bytes_sent", net_io.bytes_sent)
        self.metrics.record_metric("system.network.bytes_recv", net_io.bytes_recv)
        
        # Process count
        process_count = len(psutil.pids())
        self.metrics.record_metric("system.processes.count", process_count)

class AlertManager:
    """Alert management system"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alerts: Dict[str, Alert] = {}
        self.alert_events: List[AlertEvent] = []
        self.lock = threading.Lock()
    
    def add_alert(self, alert: Alert):
        """Add an alert definition"""
        with self.lock:
            self.alerts[alert.id] = alert
    
    def remove_alert(self, alert_id: str):
        """Remove an alert definition"""
        with self.lock:
            if alert_id in self.alerts:
                del self.alerts[alert_id]
    
    def check_alerts(self) -> List[AlertEvent]:
        """Check all alerts and return triggered events"""
        triggered_events = []
        current_time = datetime.now()
        
        with self.lock:
            for alert_id, alert in self.alerts.items():
                if not alert.enabled:
                    continue
                
                # Check cooldown
                if alert.last_triggered:
                    cooldown_end = alert.last_triggered + timedelta(minutes=alert.cooldown_minutes)
                    if current_time < cooldown_end:
                        continue
                
                # Get current metric value
                summary = self.metrics.get_metric_summary(alert.condition, minutes=5)
                current_value = summary.get("latest", 0)
                
                # Check threshold
                threshold_exceeded = False
                if alert.condition.startswith("system.cpu.usage") and current_value > alert.threshold:
                    threshold_exceeded = True
                elif alert.condition.startswith("system.memory.usage") and current_value > alert.threshold:
                    threshold_exceeded = True
                elif alert.condition.startswith("system.disk.usage") and current_value > alert.threshold:
                    threshold_exceeded = True
                elif alert.condition.startswith("response_time") and current_value > alert.threshold:
                    threshold_exceeded = True
                elif alert.condition.startswith("error_rate") and current_value > alert.threshold:
                    threshold_exceeded = True
                
                if threshold_exceeded:
                    # Create alert event
                    event = AlertEvent(
                        alert_id=alert.id,
                        alert_name=alert.name,
                        current_value=current_value,
                        threshold=alert.threshold,
                        level=alert.level,
                        timestamp=current_time,
                        message=f"{alert.name}: {current_value:.2f} exceeds threshold {alert.threshold}"
                    )
                    
                    triggered_events.append(event)
                    self.alert_events.append(event)
                    
                    # Update last triggered time
                    alert.last_triggered = current_time
        
        return triggered_events
    
    def get_alert_events(self, hours: int = 24) -> List[AlertEvent]:
        """Get alert events from the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        with self.lock:
            return [event for event in self.alert_events if event.timestamp >= cutoff]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics"""
        with self.lock:
            total_alerts = len(self.alerts)
            enabled_alerts = sum(1 for alert in self.alerts.values() if alert.enabled)
            recent_events = len(self.get_alert_events(hours=1))
            
            return {
                "total_alerts": total_alerts,
                "enabled_alerts": enabled_alerts,
                "recent_events": recent_events,
                "alert_levels": {
                    "info": sum(1 for alert in self.alerts.values() if alert.level == AlertLevel.INFO),
                    "warning": sum(1 for alert in self.alerts.values() if alert.level == AlertLevel.WARNING),
                    "critical": sum(1 for alert in self.alerts.values() if alert.level == AlertLevel.CRITICAL)
                }
            }

class PerformanceMonitor:
    """Main performance monitoring system"""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.system_collector = SystemMetricsCollector(self.metrics)
        self.alert_manager = AlertManager(self.metrics)
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """Setup default system alerts"""
        default_alerts = [
            Alert(
                id="cpu_high",
                name="High CPU Usage",
                condition="system.cpu.usage",
                threshold=80.0,
                level=AlertLevel.WARNING
            ),
            Alert(
                id="memory_high",
                name="High Memory Usage",
                condition="system.memory.usage",
                threshold=85.0,
                level=AlertLevel.WARNING
            ),
            Alert(
                id="disk_high",
                name="High Disk Usage",
                condition="system.disk.usage",
                threshold=90.0,
                level=AlertLevel.CRITICAL
            ),
            Alert(
                id="cpu_critical",
                name="Critical CPU Usage",
                condition="system.cpu.usage",
                threshold=95.0,
                level=AlertLevel.CRITICAL
            ),
            Alert(
                id="memory_critical",
                name="Critical Memory Usage",
                condition="system.memory.usage",
                threshold=95.0,
                level=AlertLevel.CRITICAL
            )
        ]
        
        for alert in default_alerts:
            self.alert_manager.add_alert(alert)
    
    async def start_monitoring(self, collection_interval: int = 30):
        """Start performance monitoring"""
        await self.system_collector.start_collection(collection_interval)
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        await self.system_collector.stop_collection()
    
    def record_request_metric(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record request metrics"""
        tags = {
            "endpoint": endpoint,
            "method": method,
            "status_code": str(status_code)
        }
        
        self.metrics.record_timer("request.duration", duration, tags)
        self.metrics.increment_counter("request.count", 1, tags)
        
        if status_code >= 400:
            self.metrics.increment_counter("request.errors", 1, tags)
    
    def record_error(self, error_type: str, error_message: str):
        """Record error metrics"""
        tags = {"error_type": error_type}
        self.metrics.increment_counter("errors.count", 1, tags)
        self.metrics.record_metric("errors.latest", 1, tags)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        # System metrics
        cpu_summary = self.metrics.get_metric_summary("system.cpu.usage", minutes=60)
        memory_summary = self.metrics.get_metric_summary("system.memory.usage", minutes=60)
        disk_summary = self.metrics.get_metric_summary("system.disk.usage", minutes=60)
        
        # Request metrics
        request_stats = self.metrics.get_timer_stats("request.duration")
        error_count = self.metrics.counters.get("request.errors", 0)
        total_requests = self.metrics.counters.get("request.count", 0)
        
        # Alert summary
        alert_summary = self.alert_manager.get_alert_summary()
        recent_alerts = self.alert_manager.get_alert_events(hours=1)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu": cpu_summary,
                "memory": memory_summary,
                "disk": disk_summary
            },
            "requests": {
                "total": total_requests,
                "errors": error_count,
                "error_rate": (error_count / total_requests * 100) if total_requests > 0 else 0,
                "duration_stats": request_stats
            },
            "alerts": {
                "summary": alert_summary,
                "recent_events": [
                    {
                        "alert_name": event.alert_name,
                        "level": event.level.value,
                        "message": event.message,
                        "timestamp": event.timestamp.isoformat()
                    }
                    for event in recent_alerts
                ]
            }
        }
    
    def check_alerts(self) -> List[AlertEvent]:
        """Check and return triggered alerts"""
        return self.alert_manager.check_alerts()

# Global performance monitor instance
performance_monitor = PerformanceMonitor()




