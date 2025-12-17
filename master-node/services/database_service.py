"""
Database service for storing AI pipeline results
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import numpy as np
import pickle

from models.database import Detection, Track
from utils.logger import logger


class DatabaseService:
    """Database operations service"""
    
    def store_detections(
        self,
        db: Session,
        frame_id: int,
        camera_id: str,
        detections: List[Dict],
        tracked_objects: List[Dict],
        timestamp: datetime
    ):
        """
        Store detections in database
        
        Args:
            db: Database session
            frame_id: Frame ID
            camera_id: Camera ID
            detections: List of detections
            tracked_objects: List of tracked objects
            timestamp: Detection timestamp
        """
        # Create mapping from bbox to track_id
        track_map = {}
        for track in tracked_objects:
            bbox = track["bbox"]
            track_id = track["track_id"]
            # Use bbox as key (approximate match)
            bbox_key = tuple(bbox)
            track_map[bbox_key] = track_id
        
        # Store detections
        for det in detections:
            bbox = det["bbox"]
            bbox_key = tuple(bbox)
            track_id = track_map.get(bbox_key)
            
            db_detection = Detection(
                frame_id=frame_id,
                camera_id=camera_id,
                track_id=track_id,
                bbox_x=bbox[0],
                bbox_y=bbox[1],
                bbox_width=bbox[2],
                bbox_height=bbox[3],
                confidence=det["confidence"],
                class_id=det.get("class_id", 0),
                timestamp=timestamp
            )
            db.add(db_detection)
    
    def update_tracks(
        self,
        db: Session,
        camera_id: str,
        tracked_objects: List[Dict],
        reid_features: Dict[int, np.ndarray],
        timestamp: datetime
    ):
        """
        Update or create tracks in database
        
        Args:
            db: Database session
            camera_id: Camera ID
            tracked_objects: List of tracked objects
            reid_features: Dictionary of track_id -> feature vector
            timestamp: Current timestamp
        """
        for track in tracked_objects:
            track_id = track["track_id"]
            
            # Check if track exists
            db_track = db.query(Track).filter(
                Track.track_id == track_id,
                Track.camera_id == camera_id
            ).first()
            
            features = reid_features.get(track_id)
            
            if db_track:
                # Update existing track
                db_track.last_seen = timestamp
                db_track.total_frames += 1
                db_track.avg_confidence = (
                    (db_track.avg_confidence * (db_track.total_frames - 1) + track["confidence"]) /
                    db_track.total_frames
                )
                
                # Update Re-ID embedding if available
                if features is not None:
                    db_track.reid_embedding = pickle.dumps(features)
            else:
                # Create new track
                db_track = Track(
                    track_id=track_id,
                    camera_id=camera_id,
                    first_seen=timestamp,
                    last_seen=timestamp,
                    total_frames=1,
                    avg_confidence=track["confidence"],
                    reid_embedding=pickle.dumps(features) if features is not None else None
                )
                db.add(db_track)

