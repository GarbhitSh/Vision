"""
Camera management endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from models.schemas import CameraCreate, CameraResponse
from typing import Optional, List
from sqlalchemy.orm import Session
from config.database import get_db
from models.database import Camera
from fastapi import Depends

router = APIRouter()


@router.post("/cameras/register", response_model=CameraResponse)
async def register_camera(camera: CameraCreate, db: Session = Depends(get_db)):
    """
    Register a new camera
    """
    # Check if camera already exists
    existing = db.query(Camera).filter(Camera.camera_id == camera.camera_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Camera already registered")
    
    # Create new camera
    db_camera = Camera(**camera.model_dump())
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    
    return db_camera


@router.get("/cameras", response_model=dict)
async def get_cameras(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get list of all cameras
    """
    query = db.query(Camera)
    if status:
        query = query.filter(Camera.status == status)
    
    cameras = query.all()
    
    return {
        "cameras": [
            {
                "camera_id": cam.camera_id,
                "edge_node_id": cam.edge_node_id,
                "location": cam.location,
                "resolution": cam.resolution,
                "fps": cam.fps,
                "status": cam.status,
                "created_at": cam.created_at.isoformat() if cam.created_at else None
            }
            for cam in cameras
        ],
        "total": len(cameras)
    }


@router.get("/cameras/{camera_id}", response_model=CameraResponse)
async def get_camera(camera_id: str, db: Session = Depends(get_db)):
    """
    Get camera details
    """
    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    return camera

