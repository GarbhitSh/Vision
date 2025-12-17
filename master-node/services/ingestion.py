"""
Frame ingestion service
Processes incoming frames through AI pipeline
"""
import base64
import cv2
import numpy as np
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from services.detection import DetectionService
from services.tracking import TrackingService
from services.reid import ReIDService
from services.database_service import DatabaseService
from services.analytics_service import AnalyticsService
from services.risk_assessment import RiskAssessmentEngine
from services.streamer import StreamerService
from services.frame_cache import frame_cache
from models.database import Frame
from utils.logger import logger


class FrameIngestionService:
    """Frame ingestion and processing service"""
    
    def __init__(self):
        """Initialize ingestion service"""
        self.detection_service = DetectionService()
        self.tracking_service = TrackingService()
        self.reid_service = ReIDService()
        self.database_service = DatabaseService()
        self.analytics_service = AnalyticsService()
        self.risk_engine = RiskAssessmentEngine()
        self.streamer_service = StreamerService()
        logger.info("Frame ingestion service initialized")
    
    def decode_frame(self, frame_data: str) -> np.ndarray:
        """
        Decode base64 encoded frame
        
        Args:
            frame_data: Base64 encoded JPEG/PNG
        
        Returns:
            Decoded frame as numpy array (BGR)
        """
        try:
            # Decode base64
            image_bytes = base64.b64decode(frame_data)
            
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            
            # Decode image
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                raise ValueError("Failed to decode frame")
            
            return frame
        except Exception as e:
            logger.error(f"Frame decoding error: {e}")
            raise
    
    def process_frame(
        self,
        camera_id: str,
        frame_id: int,
        frame_data: str,
        timestamp: datetime,
        width: int,
        height: int,
        db: Session
    ) -> Dict:
        """
        Process frame through AI pipeline
        
        Args:
            camera_id: Camera identifier
            frame_id: Frame identifier
            frame_data: Base64 encoded frame
            timestamp: Frame timestamp
            width: Frame width
            height: Frame height
            db: Database session
        
        Returns:
            Processing results
        """
        try:
            # Decode frame
            frame = self.decode_frame(frame_data)
            
            # Verify dimensions
            if frame.shape[1] != width or frame.shape[0] != height:
                logger.warning(f"Frame dimensions mismatch: expected {width}x{height}, got {frame.shape[1]}x{frame.shape[0]}")
            
            # Store frame metadata
            db_frame = Frame(
                camera_id=camera_id,
                frame_id=frame_id,
                timestamp=timestamp,
                width=width,
                height=height
            )
            db.add(db_frame)
            db.flush()  # Get frame.id
            
            # Step 1: Detection
            detections = self.detection_service.detect(frame)
            logger.debug(f"Detected {len(detections)} people")
            
            # Step 2: Tracking
            tracked_objects = self.tracking_service.update(camera_id, detections)
            logger.debug(f"Tracking {len(tracked_objects)} objects")
            
            # Step 3: Re-ID feature extraction
            reid_features = {}
            for track in tracked_objects:
                track_id = track["track_id"]
                bbox = track["bbox"]
                
                # Extract Re-ID features
                features = self.reid_service.extract_features(frame, bbox)
                reid_features[track_id] = features
            
            # Step 4: Store detections and tracks in database
            self.database_service.store_detections(
                db, db_frame.id, camera_id, detections, tracked_objects, timestamp
            )
            
            self.database_service.update_tracks(
                db, camera_id, tracked_objects, reid_features, timestamp
            )
            
            # Step 5: Compute analytics
            analytics = self.analytics_service.compute_analytics(
                camera_id=camera_id,
                detections=detections,
                tracks=tracked_objects,
                frame_width=width,
                frame_height=height,
                fps=30.0,
                db=db
            )
            
            # Analytics already includes risk_score and risk_level from compute_analytics
            analytics_data = {
                "people_count": analytics.get("people_count", 0),
                "density": analytics.get("density", 0.0),
                "avg_speed": analytics.get("avg_speed", 0.0),
                "flow_direction": analytics.get("flow_direction"),
                "congestion_level": analytics.get("congestion_level", "low"),
                "risk_score": analytics.get("risk_score", 0.0),
                "risk_level": analytics.get("risk_level", "NORMAL")
            }
            
            # Step 7: Cache frame for streaming
            try:
                frame_cache.add_frame(
                    camera_id=camera_id,
                    frame=frame,
                    detections=detections,
                    tracks=tracked_objects,
                    analytics=analytics_data
                )
            except Exception as e:
                logger.warning(f"Failed to cache frame: {e}")
            
            db.commit()
            
            return {
                "frame_id": frame_id,
                "detections_count": len(detections),
                "tracks_count": len(tracked_objects),
                "processing_time_ms": 0  # TODO: Add timing
            }
        
        except Exception as e:
            logger.error(f"Frame processing error: {e}")
            db.rollback()
            raise

