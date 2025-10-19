"""
Metrics router for monitoring dashboard.
Exposes metrics from the audit database.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import json

router = APIRouter(prefix="/metrics", tags=["metrics"])

def get_db_connection():
    """Get database connection."""
    db_path = Path(".run/audit.db")
    if not db_path.exists():
        raise HTTPException(status_code=503, detail="Audit database not found")
    return sqlite3.connect(str(db_path))

@router.get("/summary")
async def get_metrics_summary() -> Dict[str, Any]:
    """Get summary metrics from audit database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        total = cursor.fetchone()[0]
        
        # Get OK count
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE status = 'OK'")
        ok_count = cursor.fetchone()[0]
        
        # Get ABSTAIN count
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE status = 'ABSTAIN'")
        abstain_count = cursor.fetchone()[0]
        
        # Get average confidence
        cursor.execute("SELECT AVG(confidence) FROM audit_logs WHERE confidence IS NOT NULL")
        avg_confidence = cursor.fetchone()[0] or 0
        
        # Get top standards
        cursor.execute("""
            SELECT standard, COUNT(*) as count 
            FROM audit_logs 
            WHERE standard IS NOT NULL 
            GROUP BY standard 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_standards = [{"standard": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # Get last 24h count
        yesterday = datetime.now() - timedelta(days=1)
        cursor.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE timestamp > ?", 
            (yesterday.isoformat(),)
        )
        last_24h = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total": total,
            "ok": ok_count,
            "abstain": abstain_count,
            "avg_confidence": round(avg_confidence, 3),
            "top_standards": top_standards,
            "last_24h": last_24h
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")

@router.get("/timeseries")
async def get_timeseries_metrics(
    window: str = Query("daily", description="Time window: daily, hourly, weekly")
) -> List[Dict[str, Any]]:
    """Get time series metrics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Determine time format based on window
        if window == "hourly":
            time_format = "%Y-%m-%d %H:00:00"
            group_by = "strftime('%Y-%m-%d %H:00:00', timestamp)"
        elif window == "weekly":
            time_format = "%Y-W%W"
            group_by = "strftime('%Y-W%W', timestamp)"
        else:  # daily
            time_format = "%Y-%m-%d"
            group_by = "date(timestamp)"
        
        # Get time series data
        query = f"""
            SELECT 
                {group_by} as ts,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'OK' THEN 1 ELSE 0 END) as ok,
                SUM(CASE WHEN status = 'ABSTAIN' THEN 1 ELSE 0 END) as abstain,
                AVG(confidence) as avg_confidence
            FROM audit_logs 
            WHERE timestamp >= date('now', '-30 days')
            GROUP BY {group_by}
            ORDER BY ts
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        timeseries = []
        for row in rows:
            timeseries.append({
                "ts": row[0],
                "total": row[1],
                "ok": row[2],
                "abstain": row[3],
                "avg_confidence": round(row[4] or 0, 3)
            })
        
        conn.close()
        return timeseries
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving timeseries: {str(e)}")

@router.get("/topics")
async def get_topic_metrics() -> Dict[str, Any]:
    """Get topic-level metrics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get topic counts
        cursor.execute("""
            SELECT 
                topic,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'OK' THEN 1 ELSE 0 END) as ok,
                SUM(CASE WHEN status = 'ABSTAIN' THEN 1 ELSE 0 END) as abstain,
                AVG(confidence) as avg_confidence
            FROM audit_logs 
            WHERE topic IS NOT NULL
            GROUP BY topic
            ORDER BY total DESC
        """)
        
        topics = []
        for row in cursor.fetchall():
            topics.append({
                "topic": row[0],
                "total": row[1],
                "ok": row[2],
                "abstain": row[3],
                "avg_confidence": round(row[4] or 0, 3)
            })
        
        conn.close()
        return {"topics": topics}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving topic metrics: {str(e)}")

@router.get("/confidence-distribution")
async def get_confidence_distribution() -> Dict[str, Any]:
    """Get confidence score distribution."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get confidence distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN confidence < 0.3 THEN 'low'
                    WHEN confidence < 0.7 THEN 'medium'
                    ELSE 'high'
                END as confidence_level,
                COUNT(*) as count
            FROM audit_logs 
            WHERE confidence IS NOT NULL
            GROUP BY confidence_level
        """)
        
        distribution = {}
        for row in cursor.fetchall():
            distribution[row[0]] = row[1]
        
        conn.close()
        return {"distribution": distribution}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving confidence distribution: {str(e)}")

@router.get("/recent-activity")
async def get_recent_activity(limit: int = Query(10, description="Number of recent activities")) -> List[Dict[str, Any]]:
    """Get recent activity from audit log."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                timestamp,
                endpoint,
                status,
                confidence,
                topic,
                standard,
                user_id
            FROM audit_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        activities = []
        for row in cursor.fetchall():
            activities.append({
                "timestamp": row[0],
                "endpoint": row[1],
                "status": row[2],
                "confidence": row[3],
                "topic": row[4],
                "standard": row[5],
                "user_id": row[6]
            })
        
        conn.close()
        return activities
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving recent activity: {str(e)}")
