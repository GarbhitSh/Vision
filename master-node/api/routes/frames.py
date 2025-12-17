"""
Frame ingestion endpoints
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from datetime import datetime
import base64
import time
from sqlalchemy.orm import Session

from config.database import get_db
from services.ingestion import FrameIngestionService
from utils.logger import logger

router = APIRouter()

# Initialize ingestion service (singleton)
ingestion_service = FrameIngestionService()


@router.post("/frames/upload", response_model=dict)
async def upload_frame(
    camera_id: str = Form(...),
    frame: UploadFile = File(...),
    timestamp: Optional[str] = Form(None),
    frame_id: Optional[int] = Form(0),
    db: Session = Depends(get_db)
):
    """
    Upload frame via HTTP (alternative to WebSocket)
    """
    try:
        start_time = time.time()
        
        # Read frame data
        frame_bytes = await frame.read()
        frame_data = base64.b64encode(frame_bytes).decode('utf-8')
        
        # Parse timestamp
        if timestamp:
            frame_timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            frame_timestamp = datetime.utcnow()
        
        # Get frame dimensions (would need to decode to get actual dimensions)
        # For now, use defaults or extract from image
        import cv2
        import numpy as np
        nparr = np.frombuffer(frame_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is not None:
            height, width = img.shape[:2]
        else:
            width, height = 1920, 1080  # Default
        
        # Process frame
        result = ingestion_service.process_frame(
            camera_id=camera_id,
            frame_id=frame_id,
            frame_data=frame_data,
            timestamp=frame_timestamp,
            width=width,
            height=height,
            db=db
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "status": "success",
            "frame_id": result["frame_id"],
            "processing_time_ms": processing_time,
            "detections_count": result["detections_count"],
            "tracks_count": result["tracks_count"]
        }
    
    except Exception as e:
        logger.error(f"Frame upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

