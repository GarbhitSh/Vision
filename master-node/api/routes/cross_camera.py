"""
Cross-Camera Movement API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from config.database import get_db
from models.database import CrossCameraMovement
from models.schemas import CrossCameraMovementResponse, CrossCameraMovementStatistics
from services.cross_camera_matching import CrossCameraMatcher
from utils.logger import logger

router = APIRouter()
matcher = CrossCameraMatcher()


@router.get("/movements", response_model=List[CrossCameraMovementResponse])
async def get_cross_camera_movements(
    entry_camera_id: Optional[str] = Query(None, description="Filter by entry camera ID"),
    exit_camera_id: Optional[str] = Query(None, description="Filter by exit camera ID"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Get cross-camera movement mappings
    
    Returns movements where a person entered one edge node and exited another.
    """
    try:
        movements = matcher.get_movements(
            db=db,
            entry_camera_id=entry_camera_id,
            exit_camera_id=exit_camera_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return movements
    except Exception as e:
        logger.error(f"Error fetching cross-camera movements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/movements/statistics", response_model=CrossCameraMovementStatistics)
async def get_movement_statistics(
    start_time: Optional[datetime] = Query(None, description="Filter by start time (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Get statistics about cross-camera movements
    """
    try:
        stats = matcher.get_movement_statistics(
            db=db,
            start_time=start_time,
            end_time=end_time
        )
        
        return stats
    except Exception as e:
        logger.error(f"Error fetching movement statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/movements/camera/{camera_id}", response_model=List[CrossCameraMovementResponse])
async def get_movements_by_camera(
    camera_id: str,
    direction: str = Query("both", regex="^(entry|exit|both)$", description="Filter by direction"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get cross-camera movements for a specific camera
    
    - **direction**: "entry" (where people entered this camera), "exit" (where people exited this camera), or "both"
    - **hours**: How many hours to look back
    """
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        if direction == "entry":
            movements = matcher.get_movements(
                db=db,
                entry_camera_id=camera_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
        elif direction == "exit":
            movements = matcher.get_movements(
                db=db,
                exit_camera_id=camera_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
        else:  # both
            # Get movements where camera is entry or exit
            entry_movements = matcher.get_movements(
                db=db,
                entry_camera_id=camera_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            exit_movements = matcher.get_movements(
                db=db,
                exit_camera_id=camera_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            # Combine and deduplicate
            movement_dict = {}
            for m in entry_movements + exit_movements:
                if m.id not in movement_dict:
                    movement_dict[m.id] = m
            movements = list(movement_dict.values())
            movements.sort(key=lambda x: x.entry_timestamp, reverse=True)
            movements = movements[:limit]
        
        return movements
    except Exception as e:
        logger.error(f"Error fetching movements for camera {camera_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/movements/pair/{camera1_id}/{camera2_id}", response_model=List[CrossCameraMovementResponse])
async def get_movements_between_cameras(
    camera1_id: str,
    camera2_id: str,
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get movements between two specific cameras
    
    Returns movements where a person entered camera1 and exited camera2, or vice versa.
    """
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get movements in both directions
        movements_1_to_2 = matcher.get_movements(
            db=db,
            entry_camera_id=camera1_id,
            exit_camera_id=camera2_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        movements_2_to_1 = matcher.get_movements(
            db=db,
            entry_camera_id=camera2_id,
            exit_camera_id=camera1_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        # Combine and sort
        movements = movements_1_to_2 + movements_2_to_1
        movements.sort(key=lambda x: x.entry_timestamp, reverse=True)
        
        return movements[:limit]
    except Exception as e:
        logger.error(f"Error fetching movements between {camera1_id} and {camera2_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

