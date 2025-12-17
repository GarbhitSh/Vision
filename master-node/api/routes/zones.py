"""
Zone management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from models.schemas import ZoneCreate, ZoneResponse
from sqlalchemy.orm import Session
from typing import List
import json

from config.database import get_db
from models.database import Zone, Camera, Detection
from services.analytics import AnalyticsEngine
from utils.logger import logger

router = APIRouter()

analytics_engine = AnalyticsEngine()


@router.post("/zones", response_model=ZoneResponse)
async def create_zone(
    zone: ZoneCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new zone
    """
    try:
        # Verify camera exists
        camera = db.query(Camera).filter(Camera.camera_id == zone.camera_id).first()
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        # Create zone
        db_zone = Zone(
            camera_id=zone.camera_id,
            zone_name=zone.zone_name,
            zone_type=zone.zone_type,
            polygon_coords=json.dumps(zone.polygon_coords),
            max_capacity=zone.max_capacity,
            current_occupancy=0,
            status="active"
        )
        
        db.add(db_zone)
        db.commit()
        db.refresh(db_zone)
        
        return ZoneResponse(
            id=db_zone.id,
            camera_id=db_zone.camera_id,
            zone_name=db_zone.zone_name,
            zone_type=db_zone.zone_type,
            polygon_coords=json.loads(db_zone.polygon_coords) if isinstance(db_zone.polygon_coords, str) else db_zone.polygon_coords,
            max_capacity=db_zone.max_capacity,
            current_occupancy=db_zone.current_occupancy,
            status=db_zone.status
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating zone: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/zones/{camera_id}", response_model=dict)
async def get_zones(
    camera_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all zones for a camera
    """
    try:
        # Verify camera exists
        camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        # Get zones
        zones = db.query(Zone).filter(
            Zone.camera_id == camera_id,
            Zone.status == "active"
        ).all()
        
        # Calculate current occupancy for each zone
        # Get latest detections
        from datetime import datetime, timedelta
        recent_time = datetime.utcnow() - timedelta(seconds=5)
        
        latest_detections = db.query(Detection).filter(
            Detection.camera_id == camera_id,
            Detection.timestamp >= recent_time
        ).all()
        
        # Calculate occupancy per zone
        zone_occupancy = {}
        for zone in zones:
            polygon_coords = json.loads(zone.polygon_coords) if isinstance(zone.polygon_coords, str) else zone.polygon_coords
            
            count = 0
            for det in latest_detections:
                cx = det.bbox_x + det.bbox_width / 2
                cy = det.bbox_y + det.bbox_height / 2
                
                if analytics_engine._point_in_polygon(int(cx), int(cy), polygon_coords):
                    count += 1
            
            zone_occupancy[zone.id] = count
        
        return {
            "zones": [
                {
                    "id": zone.id,
                    "camera_id": zone.camera_id,
                    "zone_name": zone.zone_name,
                    "zone_type": zone.zone_type,
                    "polygon_coords": json.loads(zone.polygon_coords) if isinstance(zone.polygon_coords, str) else zone.polygon_coords,
                    "max_capacity": zone.max_capacity,
                    "current_occupancy": zone_occupancy.get(zone.id, 0),
                    "status": zone.status
                }
                for zone in zones
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting zones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/zones/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: int,
    zone: ZoneCreate,
    db: Session = Depends(get_db)
):
    """
    Update a zone
    """
    try:
        db_zone = db.query(Zone).filter(Zone.id == zone_id).first()
        if not db_zone:
            raise HTTPException(status_code=404, detail="Zone not found")
        
        # Update zone
        db_zone.zone_name = zone.zone_name
        db_zone.zone_type = zone.zone_type
        db_zone.polygon_coords = json.dumps(zone.polygon_coords)
        db_zone.max_capacity = zone.max_capacity
        
        db.commit()
        db.refresh(db_zone)
        
        return ZoneResponse(
            id=db_zone.id,
            camera_id=db_zone.camera_id,
            zone_name=db_zone.zone_name,
            zone_type=db_zone.zone_type,
            polygon_coords=json.loads(db_zone.polygon_coords) if isinstance(db_zone.polygon_coords, str) else db_zone.polygon_coords,
            max_capacity=db_zone.max_capacity,
            current_occupancy=db_zone.current_occupancy,
            status=db_zone.status
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating zone: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/zones/{zone_id}", response_model=dict)
async def delete_zone(
    zone_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a zone (soft delete - set status to inactive)
    """
    try:
        db_zone = db.query(Zone).filter(Zone.id == zone_id).first()
        if not db_zone:
            raise HTTPException(status_code=404, detail="Zone not found")
        
        # Soft delete
        db_zone.status = "inactive"
        db.commit()
        
        return {
            "status": "deleted",
            "zone_id": zone_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting zone: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

