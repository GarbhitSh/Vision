"""
Alerts endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from config.database import get_db
from models.database import Alert
from utils.logger import logger

router = APIRouter()


@router.get("/alerts/active", response_model=dict)
async def get_active_alerts(
    camera_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get active alerts
    """
    try:
        query = db.query(Alert).filter(Alert.acknowledged == False)
        
        # Filter by camera
        if camera_id:
            query = query.filter(Alert.camera_id == camera_id)
        
        # Filter by severity
        if severity:
            query = query.filter(Alert.severity == severity.upper())
        
        # Get recent alerts (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        query = query.filter(Alert.timestamp >= cutoff_time)
        
        # Order by timestamp (newest first) and limit
        alerts = query.order_by(Alert.timestamp.desc()).limit(limit).all()
        
        return {
            "alerts": [
                {
                    "id": alert.id,
                    "camera_id": alert.camera_id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "risk_score": alert.risk_score,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "acknowledged": alert.acknowledged
                }
                for alert in alerts
            ],
            "total": len(alerts)
        }
    
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge", response_model=dict)
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Acknowledge an alert
    """
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.acknowledged = True
        db.commit()
        
        return {
            "status": "acknowledged",
            "alert_id": alert_id,
            "acknowledged_at": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

