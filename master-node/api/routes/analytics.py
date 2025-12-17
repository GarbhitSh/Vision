"""
Analytics endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import base64
import cv2
import numpy as np

from config.database import get_db
from services.analytics_service import AnalyticsService
from services.analytics import AnalyticsEngine
from models.database import Detection, Camera
from utils.logger import logger

router = APIRouter()

# Initialize services
analytics_service = AnalyticsService()
analytics_engine = AnalyticsEngine()


@router.get("/analytics/{camera_id}/realtime", response_model=dict)
async def get_realtime_metrics(
    camera_id: str,
    db: Session = Depends(get_db)
):
    """
    Get real-time analytics metrics for a camera
    """
    try:
        # Verify camera exists
        camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        # Get real-time analytics
        analytics = analytics_service.get_realtime_analytics(camera_id, db)
        
        return analytics
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting realtime analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/{camera_id}/history", response_model=dict)
async def get_historical_analytics(
    camera_id: str,
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    interval: int = Query(60, ge=1),
    db: Session = Depends(get_db)
):
    """
    Get historical analytics data
    """
    try:
        # Verify camera exists
        camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        # Parse timestamps
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except:
                start_dt = datetime.utcnow() - timedelta(hours=1)
        else:
            start_dt = datetime.utcnow() - timedelta(hours=1)
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except:
                end_dt = datetime.utcnow()
        else:
            end_dt = datetime.utcnow()
        
        # Get historical analytics
        data = analytics_service.get_historical_analytics(
            camera_id=camera_id,
            start_time=start_dt,
            end_time=end_dt,
            interval_seconds=interval,
            db=db
        )
        
        return {
            "camera_id": camera_id,
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "interval": interval,
            "data": data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/{camera_id}/heatmap", response_model=dict)
async def get_heatmap(
    camera_id: str,
    duration: int = Query(300, ge=1),
    db: Session = Depends(get_db)
):
    """
    Get heatmap data for a camera
    """
    try:
        # Verify camera exists
        camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        # Get detections in time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(seconds=duration)
        
        detections = db.query(Detection).join(Detection.frame).filter(
            Detection.camera_id == camera_id,
            Detection.timestamp >= start_time,
            Detection.timestamp <= end_time
        ).all()
        
        # Get frame dimensions (use camera resolution or default)
        if camera.resolution:
            try:
                width, height = map(int, camera.resolution.split('x'))
            except:
                width, height = 1920, 1080
        else:
            width, height = 1920, 1080
        
        # Create heatmap
        heatmap = np.zeros((height, width), dtype=np.float32)
        
        for det in detections:
            x = int(det.bbox_x)
            y = int(det.bbox_y)
            w = int(det.bbox_width)
            h = int(det.bbox_height)
            
            cx = x + w // 2
            cy = y + h // 2
            
            # Clamp to frame bounds
            cx = max(0, min(cx, width - 1))
            cy = max(0, min(cy, height - 1))
            
            # Add to heatmap (Gaussian kernel)
            kernel_size = min(max(w, h), 100)
            if kernel_size > 0:
                y_coords, x_coords = np.ogrid[:kernel_size, :kernel_size]
                center = kernel_size // 2
                sigma = kernel_size / 3.0
                kernel = np.exp(-((x_coords - center)**2 + (y_coords - center)**2) / (2 * sigma**2))
                
                y_start = max(0, cy - kernel_size // 2)
                y_end = min(height, cy + kernel_size // 2)
                x_start = max(0, cx - kernel_size // 2)
                x_end = min(width, cx + kernel_size // 2)
                
                if y_end > y_start and x_end > x_start:
                    heatmap[y_start:y_end, x_start:x_end] += kernel[
                        :y_end-y_start, :x_end-x_start
                    ]
        
        # Normalize heatmap
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()
        
        # Apply colormap
        heatmap_colored = cv2.applyColorMap(
            (heatmap * 255).astype(np.uint8),
            cv2.COLORMAP_JET
        )
        
        # Encode to base64
        _, buffer = cv2.imencode('.jpg', heatmap_colored)
        heatmap_b64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            "camera_id": camera_id,
            "heatmap": heatmap_b64,
            "resolution": {"width": width, "height": height},
            "timestamp": end_time.isoformat(),
            "duration": duration
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))

