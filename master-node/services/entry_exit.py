"""
Entry/Exit Detection Service
Tracks when objects enter or exit zones
"""
import json
import numpy as np
from typing import Dict, List, Set, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models.database import Zone, EntryExitLog, Track
from services.analytics import AnalyticsEngine
from services.cross_camera_matching import CrossCameraMatcher
from utils.logger import logger


class EntryExitDetector:
    """Detects entry/exit events for zones"""
    
    def __init__(self):
        """Initialize entry/exit detector"""
        self.analytics_engine = AnalyticsEngine()
        self.cross_camera_matcher = CrossCameraMatcher()
        # Track which objects are currently in each zone
        # camera_id -> zone_id -> set of track_ids
        self.zone_occupants: Dict[str, Dict[int, Set[int]]] = {}
    
    def detect_entry_exit(
        self,
        camera_id: str,
        tracks: List[Dict],
        zones: List[Zone],
        timestamp: datetime,
        db: Session
    ) -> Dict[str, int]:
        """
        Detect entry/exit events for zones
        
        Args:
            camera_id: Camera identifier
            tracks: List of current tracked objects
            zones: List of zone objects from database
            timestamp: Current frame timestamp
            db: Database session
        
        Returns:
            Dictionary with entry_count and exit_count
        """
        if camera_id not in self.zone_occupants:
            self.zone_occupants[camera_id] = {}
        
        entry_count = 0
        exit_count = 0
        
        # Process each zone
        for zone in zones:
            zone_id = zone.id
            zone_type = zone.zone_type
            
            # Only process entry/exit zones
            if zone_type not in ["entry", "exit"]:
                continue
            
            # Initialize zone occupants if needed
            if zone_id not in self.zone_occupants[camera_id]:
                self.zone_occupants[camera_id][zone_id] = set()
            
            # Parse polygon coordinates
            try:
                if isinstance(zone.polygon_coords, str):
                    polygon_coords = json.loads(zone.polygon_coords)
                else:
                    polygon_coords = zone.polygon_coords
                
                if not polygon_coords or len(polygon_coords) < 3:
                    continue
                
                # Convert to numpy array for point_in_polygon
                polygon = np.array(polygon_coords, dtype=np.int32)
            except Exception as e:
                logger.warning(f"Failed to parse polygon for zone {zone_id}: {e}")
                continue
            
            # Get current occupants in this zone
            current_occupants = set()
            
            # Check which tracks are currently in the zone
            for track in tracks:
                track_id = track["track_id"]
                bbox = track["bbox"]
                
                # Calculate center point
                cx = int(bbox[0] + bbox[2] / 2)
                cy = int(bbox[1] + bbox[3] / 2)
                
                # Check if center point is in polygon
                if self.analytics_engine._point_in_polygon(cx, cy, polygon):
                    current_occupants.add(track_id)
            
            # Get previous occupants
            previous_occupants = self.zone_occupants[camera_id][zone_id]
            
            # Detect entries (new occupants)
            new_entries = current_occupants - previous_occupants
            for track_id in new_entries:
                # Log entry event
                entry_event = self._log_event(
                    db=db,
                    camera_id=camera_id,
                    zone_id=zone_id,
                    zone_name=zone.zone_name,
                    track_id=track_id,
                    event_type="entry",
                    timestamp=timestamp
                )
                entry_count += 1
                logger.debug(f"Entry detected: track {track_id} entered zone {zone_id} ({zone.zone_name})")
                
                # Try to match with exit events from other cameras
                if entry_event:
                    try:
                        self.cross_camera_matcher.match_entry_to_exit(entry_event, db)
                        db.commit()
                    except Exception as e:
                        logger.warning(f"Cross-camera matching failed for entry {entry_event.id}: {e}")
                        db.rollback()
            
            # Detect exits (previous occupants no longer in zone)
            new_exits = previous_occupants - current_occupants
            for track_id in new_exits:
                # Log exit event
                exit_event = self._log_event(
                    db=db,
                    camera_id=camera_id,
                    zone_id=zone_id,
                    zone_name=zone.zone_name,
                    track_id=track_id,
                    event_type="exit",
                    timestamp=timestamp
                )
                exit_count += 1
                logger.debug(f"Exit detected: track {track_id} exited zone {zone_id} ({zone.zone_name})")
                
                # Try to match with entry events from other cameras
                if exit_event:
                    try:
                        self.cross_camera_matcher.match_exit_to_entry(exit_event, db)
                        db.commit()
                    except Exception as e:
                        logger.warning(f"Cross-camera matching failed for exit {exit_event.id}: {e}")
                        db.rollback()
            
            # Update zone occupants
            self.zone_occupants[camera_id][zone_id] = current_occupants
        
        return {
            "entry_count": entry_count,
            "exit_count": exit_count
        }
    
    def _log_event(
        self,
        db: Session,
        camera_id: str,
        zone_id: int,
        zone_name: str,
        track_id: int,
        event_type: str,
        timestamp: datetime
    ) -> Optional[EntryExitLog]:
        """Log entry/exit event to database"""
        try:
            event = EntryExitLog(
                camera_id=camera_id,
                zone_id=zone_id,
                track_id=track_id,
                event_type=event_type,
                timestamp=timestamp
            )
            db.add(event)
            db.flush()  # Get event.id
            logger.info(f"{event_type.upper()}: track {track_id} in zone '{zone_name}' (zone_id: {zone_id})")
            return event
        except Exception as e:
            logger.error(f"Failed to log entry/exit event: {e}")
            return None
    
    def cleanup_old_tracks(self, camera_id: str, active_track_ids: Set[int]):
        """
        Clean up tracking data for tracks that no longer exist
        
        Args:
            camera_id: Camera identifier
            active_track_ids: Set of currently active track IDs
        """
        if camera_id not in self.zone_occupants:
            return
        
        # Remove inactive tracks from zone occupants
        for zone_id in self.zone_occupants[camera_id]:
            self.zone_occupants[camera_id][zone_id] = (
                self.zone_occupants[camera_id][zone_id] & active_track_ids
            )

