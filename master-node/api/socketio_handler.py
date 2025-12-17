"""
Socket.IO handler for frame reception from edge nodes
"""
import socketio
import json
from datetime import datetime
from sqlalchemy.orm import Session
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

from config.database import SessionLocal
from services.ingestion import FrameIngestionService
from utils.logger import logger

# Create Socket.IO server
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode='asgi')
socketio_app = socketio.ASGIApp(sio)

# Initialize ingestion service
ingestion_service = FrameIngestionService()


@sio.on('connect')
async def connect(sid, environ):
    """Handle client connection"""
    logger.info(f"Socket.IO client connected: {sid}")


@sio.on('disconnect')
async def disconnect(sid):
    """Handle client disconnection"""
    logger.info(f"Socket.IO client disconnected: {sid}")


@sio.on('frame')
async def handle_frame(sid, data):
    """Handle frame data from edge node"""
    db = SessionLocal()
    
    try:
        # Parse message (could be string or dict)
        if isinstance(data, str):
            message = json.loads(data)
        else:
            message = data
        
        # Extract frame data
        camera_id = message.get("camera_id")
        frame_id = message.get("frame_id", 0)
        frame_data = message.get("frame_data")
        timestamp_str = message.get("timestamp")
        width = message.get("width", 1920)
        height = message.get("height", 1080)
        fps = message.get("fps", 30.0)
        
        if not camera_id or not frame_data:
            logger.warning(f"Invalid frame message from {sid}: missing camera_id or frame_data")
            try:
                await sio.emit('response', {
                    "status": "error",
                    "message": "Missing camera_id or frame_data"
                }, room=sid)
            except:
                pass
            return
        
        # Parse timestamp
        try:
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()
        except:
            timestamp = datetime.utcnow()
        
        # Process frame (with timeout protection)
        start_time = time.time()
        try:
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
            
            # Log slow processing
            if processing_time > 1000:  # > 1 second
                logger.warning(f"Slow frame processing: {processing_time:.1f}ms for frame {frame_id}")
            
            # Send response (non-blocking)
            try:
                await sio.emit('response', {
                    "status": "received",
                    "frame_id": frame_id,
                    "processing_time_ms": processing_time,
                    "detections_count": result["detections_count"],
                    "tracks_count": result["tracks_count"]
                }, room=sid)
            except Exception as emit_error:
                logger.warning(f"Failed to send response to {sid}: {emit_error}")
        
        except Exception as process_error:
            logger.error(f"Frame processing error for camera {camera_id}, frame {frame_id}: {process_error}")
            import traceback
            traceback.print_exc()
            # Don't disconnect on processing errors, just log them
            try:
                await sio.emit('response', {
                    "status": "error",
                    "message": f"Processing error: {str(process_error)[:100]}"  # Truncate long errors
                }, room=sid)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Socket.IO frame handler error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await sio.emit('response', {
                "status": "error",
                "message": str(e)[:100]  # Truncate long errors
            }, room=sid)
        except:
            pass
    finally:
        try:
            db.close()
        except:
            pass


def setup_socketio(app):
    """Setup Socket.IO with FastAPI app"""
    # Mount Socket.IO app at /socket.io/
    app.mount("/socket.io", socketio_app)
    logger.info("Socket.IO handler setup complete")

