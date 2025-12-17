"""
WebSocket handlers
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import json
import asyncio
from datetime import datetime
import time

from config.database import SessionLocal
from services.ingestion import FrameIngestionService
from utils.logger import logger

router = APIRouter()

# Initialize ingestion service (singleton)
ingestion_service = FrameIngestionService()


def get_db_session():
    """Get database session for WebSocket"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.websocket("/ws/frames")
async def websocket_frames(websocket: WebSocket):
    """
    WebSocket endpoint for receiving frames from edge nodes
    """
    await websocket.accept()
    db = SessionLocal()
    
    try:
        while True:
            # Socket.IO uses different message format
            # Try to receive as text first (for Socket.IO JSON)
            try:
                data = await websocket.receive_text()
            except:
                # Fallback to bytes if needed
                data_bytes = await websocket.receive_bytes()
                data = data_bytes.decode('utf-8')
            
            message = json.loads(data)
            
            try:
                # Extract frame data
                camera_id = message.get("camera_id")
                frame_id = message.get("frame_id", 0)
                frame_data = message.get("frame_data")
                timestamp_str = message.get("timestamp")
                width = message.get("width", 1920)
                height = message.get("height", 1080)
                
                if not camera_id or not frame_data:
                    await websocket.send_json({
                        "status": "error",
                        "message": "Missing camera_id or frame_data"
                    })
                    continue
                
                # Parse timestamp
                try:
                    if timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = datetime.utcnow()
                except:
                    timestamp = datetime.utcnow()
                
                # Process frame
                start_time = time.time()
                result = ingestion_service.process_frame(
                    camera_id=camera_id,
                    frame_id=frame_id,
                    frame_data=frame_data,
                    timestamp=timestamp,
                    width=width,
                    height=height,
                    db=db
                )
                processing_time = (time.time() - start_time) * 1000
                
                # Send response
                await websocket.send_json({
                    "status": "received",
                    "frame_id": frame_id,
                    "processing_time_ms": processing_time,
                    "detections_count": result["detections_count"],
                    "tracks_count": result["tracks_count"]
                })
            
            except Exception as e:
                logger.error(f"WebSocket frame processing error: {e}")
                import traceback
                traceback.print_exc()
                try:
                    await websocket.send_json({
                        "status": "error",
                        "message": str(e)
                    })
                except:
                    pass
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    finally:
        db.close()


@router.websocket("/ws/dashboard/{camera_id}")
async def websocket_dashboard(websocket: WebSocket, camera_id: str):
    """
    WebSocket endpoint for real-time metrics to dashboard
    """
    await websocket.accept()
    try:
        while True:
            # TODO: Send real-time metrics in Phase 3
            await websocket.send_json({
                "type": "metrics",
                "camera_id": camera_id,
                "data": {},
                "timestamp": "2024-01-01T12:00:00Z"
            })
            await asyncio.sleep(1)  # Send updates every second
    except WebSocketDisconnect:
        print("Dashboard client disconnected")


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for alert stream
    """
    await websocket.accept()
    try:
        while True:
            # TODO: Send alerts in Phase 3
            await websocket.send_json({
                "type": "alert",
                "alert": {}
            })
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Alerts client disconnected")

