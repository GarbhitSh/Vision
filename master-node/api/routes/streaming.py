"""
Video streaming endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Tuple
import cv2
import numpy as np
from datetime import datetime, timedelta
import json

from config.database import get_db
from models.database import Camera, Detection, Track, Zone, Analytics
from services.streamer import StreamerService
from services.analytics_service import AnalyticsService
from utils.logger import logger

router = APIRouter()

# Initialize services
streamer_service = StreamerService()
analytics_service = AnalyticsService()


def get_latest_detections_and_tracks(
    db: Session,
    camera_id: str,
    seconds: int = 2
) -> Tuple[List[Dict], List[Dict]]:
    """Get latest detections and tracks for camera - only active tracks from most recent frame"""
    cutoff_time = datetime.utcnow() - timedelta(seconds=seconds)
    
    # Get latest frame
    from models.database import Frame
    latest_frame = db.query(Frame).filter(
        Frame.camera_id == camera_id,
        Frame.timestamp >= cutoff_time
    ).order_by(Frame.timestamp.desc()).first()
    
    if not latest_frame:
        return [], []
    
    # Get detections for this frame (only active detections from current frame)
    detections = db.query(Detection).filter(
        Detection.frame_id == latest_frame.id
    ).all()
    
    detections_list = [
        {
            "bbox": [d.bbox_x, d.bbox_y, d.bbox_width, d.bbox_height],
            "confidence": d.confidence,
            "class_id": d.class_id,
            "track_id": d.track_id
        }
        for d in detections
    ]
    
    # Only get tracks that have detections in the latest frame (active tracks)
    # This ensures we don't show tracks for people who have left
    active_track_ids = {d.track_id for d in detections if d.track_id is not None}
    
    tracks_list = []
    for track_id in active_track_ids:
        # Get the detection for this track from the latest frame
        track_det = db.query(Detection).filter(
            Detection.frame_id == latest_frame.id,
            Detection.track_id == track_id
        ).first()
        
        if track_det:
            tracks_list.append({
                "track_id": track_id,
                "bbox": [track_det.bbox_x, track_det.bbox_y, track_det.bbox_width, track_det.bbox_height],
                "confidence": track_det.confidence,
                "state": "confirmed"
            })
    
    return detections_list, tracks_list


@router.get("/stream/{camera_id}")
async def stream_video(
    camera_id: str,
    show_heatmap: bool = Query(False),
    show_zones: bool = Query(True),
    show_track_ids: bool = Query(True),
    show_metrics: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    MJPEG video stream endpoint
    
    Args:
        camera_id: Camera identifier
        show_heatmap: Show heatmap overlay
        show_zones: Show zone boundaries
        show_track_ids: Show track IDs
        show_metrics: Show metrics overlay
    """
    # Verify camera exists
    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    async def generate_frames():
        """Generator function for MJPEG stream"""
        try:
            from services.frame_cache import frame_cache
            
            while True:
                # Try to get frame from cache first
                cached_frame_data = frame_cache.get_latest_frame(camera_id)
                
                if cached_frame_data:
                    # Use cached frame
                    frame = cached_frame_data["frame"]
                    detections = cached_frame_data["detections"]
                    tracks = cached_frame_data["tracks"]
                    analytics = cached_frame_data["analytics"]
                else:
                    # Fallback: get from database
                    detections, tracks = get_latest_detections_and_tracks(db, camera_id, seconds=2)
                    analytics = analytics_service.get_realtime_analytics(camera_id, db)
                    
                    # Create placeholder frame
                    if camera.resolution:
                        try:
                            width, height = map(int, camera.resolution.split('x'))
                        except:
                            width, height = 1920, 1080
                    else:
                        width, height = 1920, 1080
                    
                    frame = np.zeros((height, width, 3), dtype=np.uint8)
                    
                    # Add placeholder text
                    cv2.putText(
                        frame,
                        f"Camera: {camera_id} - Waiting for frames...",
                        (width // 2 - 200, height // 2),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (255, 255, 255),
                        2
                    )
                
                # Get zones
                zones = db.query(Zone).filter(
                    Zone.camera_id == camera_id,
                    Zone.status == "active"
                ).all()
                
                zones_list = [
                    {
                        "id": z.id,
                        "zone_name": z.zone_name,
                        "polygon_coords": json.loads(z.polygon_coords) if isinstance(z.polygon_coords, str) else z.polygon_coords,
                        "max_capacity": z.max_capacity,
                        "current_occupancy": 0
                    }
                    for z in zones
                ]
                
                # Annotate frame
                annotated_frame = streamer_service.annotate_frame(
                    frame=frame,
                    detections=detections,
                    tracks=tracks,
                    analytics=analytics,
                    zones=zones_list,
                    show_heatmap=show_heatmap,
                    show_zones=show_zones,
                    show_track_ids=show_track_ids,
                    show_metrics=show_metrics
                )
                
                # Encode to JPEG
                jpeg_bytes = streamer_service.encode_frame_jpeg(annotated_frame, quality=85)
                
                # Yield MJPEG frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
                
                # Small delay to control frame rate
                import asyncio
                await asyncio.sleep(0.033)  # ~30 FPS
        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            import traceback
            traceback.print_exc()
    
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/cameras/{camera_id}/snapshot")
async def get_snapshot(
    camera_id: str,
    annotated: bool = Query(True),
    show_heatmap: bool = Query(False),
    show_zones: bool = Query(True),
    show_track_ids: bool = Query(True),
    show_metrics: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Get snapshot image
    
    Args:
        camera_id: Camera identifier
        annotated: Include annotations
        show_heatmap: Show heatmap overlay
        show_zones: Show zone boundaries
        show_track_ids: Show track IDs
        show_metrics: Show metrics overlay
    """
    try:
        # Verify camera exists
        camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")
        
        # Get latest detections and tracks
        detections, tracks = get_latest_detections_and_tracks(db, camera_id, seconds=5)
        
        # Get zones
        zones = db.query(Zone).filter(
            Zone.camera_id == camera_id,
            Zone.status == "active"
        ).all()
        
        zones_list = [
            {
                "id": z.id,
                "zone_name": z.zone_name,
                "polygon_coords": json.loads(z.polygon_coords) if isinstance(z.polygon_coords, str) else z.polygon_coords,
                "max_capacity": z.max_capacity,
                "current_occupancy": 0
            }
            for z in zones
        ]
        
        # Get latest analytics
        analytics = analytics_service.get_realtime_analytics(camera_id, db)
        
        # Create frame (placeholder - would get from camera in production)
        if camera.resolution:
            try:
                width, height = map(int, camera.resolution.split('x'))
            except:
                width, height = 1920, 1080
        else:
            width, height = 1920, 1080
        
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add placeholder text
        cv2.putText(
            frame,
            f"Camera: {camera_id}",
            (width // 2 - 100, height // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
        
        # Annotate if requested
        if annotated:
            frame = streamer_service.annotate_frame(
                frame=frame,
                detections=detections,
                tracks=tracks,
                analytics=analytics,
                zones=zones_list,
                show_heatmap=show_heatmap,
                show_zones=show_zones,
                show_track_ids=show_track_ids,
                show_metrics=show_metrics
            )
        
        # Encode to JPEG
        jpeg_bytes = streamer_service.encode_frame_jpeg(frame, quality=95)
        
        from fastapi.responses import Response
        return Response(content=jpeg_bytes, media_type="image/jpeg")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Snapshot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

