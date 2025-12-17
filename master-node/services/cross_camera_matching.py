"""
Cross-Camera Matching Service
Matches people across different edge nodes using Re-ID features
"""
import pickle
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.database import EntryExitLog, Track, CrossCameraMovement, Zone
from services.reid import ReIDService
from utils.logger import logger


class CrossCameraMatcher:
    """Matches entry/exit events across different cameras"""
    
    def __init__(self):
        """Initialize cross-camera matcher"""
        self.reid_service = ReIDService()
        # Configuration
        self.similarity_threshold = 0.7  # Minimum similarity for matching
        self.max_time_window = timedelta(minutes=10)  # Max time between entry and exit
        self.match_cache: Dict[str, Dict] = {}  # Cache for recent matches
    
    def match_entry_to_exit(
        self,
        entry_event: EntryExitLog,
        db: Session
    ) -> Optional[CrossCameraMovement]:
        """
        Match an entry event to a potential exit event in another camera
        
        Args:
            entry_event: Entry event from entry_exit_logs
            db: Database session
        
        Returns:
            CrossCameraMovement if match found, None otherwise
        """
        try:
            # Get track for entry event
            entry_track = db.query(Track).filter(
                Track.track_id == entry_event.track_id,
                Track.camera_id == entry_event.camera_id
            ).first()
            
            if not entry_track or not entry_track.reid_embedding:
                logger.debug(f"No Re-ID features for entry track {entry_event.track_id}")
                return None
            
            # Deserialize Re-ID features
            entry_features = pickle.loads(entry_track.reid_embedding)
            
            # Find potential exit events from other cameras
            # Look for exit events within time window
            time_window_start = entry_event.timestamp
            time_window_end = entry_event.timestamp + self.max_time_window
            
            # Query exit events from other cameras
            exit_events = db.query(EntryExitLog).filter(
                EntryExitLog.event_type == "exit",
                EntryExitLog.camera_id != entry_event.camera_id,
                EntryExitLog.timestamp >= time_window_start,
                EntryExitLog.timestamp <= time_window_end
            ).order_by(EntryExitLog.timestamp.asc()).all()
            
            if not exit_events:
                logger.debug(f"No exit events found for entry {entry_event.id}")
                return None
            
            # Match against exit events
            best_match = None
            best_similarity = 0.0
            
            for exit_event in exit_events:
                # Get track for exit event
                exit_track = db.query(Track).filter(
                    Track.track_id == exit_event.track_id,
                    Track.camera_id == exit_event.camera_id
                ).first()
                
                if not exit_track or not exit_track.reid_embedding:
                    continue
                
                # Deserialize Re-ID features
                exit_features = pickle.loads(exit_track.reid_embedding)
                
                # Compute similarity
                similarity = self.reid_service.compute_similarity(
                    entry_features, exit_features
                )
                
                # Check if this is a better match
                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_match = exit_event
            
            if best_match:
                # Create cross-camera movement record
                duration = (best_match.timestamp - entry_event.timestamp).total_seconds()
                match_confidence = self._get_confidence_level(best_similarity)
                
                movement = CrossCameraMovement(
                    entry_camera_id=entry_event.camera_id,
                    entry_zone_id=entry_event.zone_id,
                    entry_track_id=entry_event.track_id,
                    entry_timestamp=entry_event.timestamp,
                    exit_camera_id=best_match.camera_id,
                    exit_zone_id=best_match.zone_id,
                    exit_track_id=best_match.track_id,
                    exit_timestamp=best_match.timestamp,
                    similarity_score=best_similarity,
                    match_confidence=match_confidence,
                    duration_seconds=duration
                )
                
                db.add(movement)
                logger.info(
                    f"Cross-camera match: {entry_event.camera_id} (track {entry_event.track_id}) -> "
                    f"{best_match.camera_id} (track {best_match.track_id}), "
                    f"similarity: {best_similarity:.3f}, duration: {duration:.1f}s"
                )
                
                return movement
            
            return None
            
        except Exception as e:
            logger.error(f"Error matching entry to exit: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def match_exit_to_entry(
        self,
        exit_event: EntryExitLog,
        db: Session
    ) -> Optional[CrossCameraMovement]:
        """
        Match an exit event to a potential entry event in another camera
        
        Args:
            exit_event: Exit event from entry_exit_logs
            db: Database session
        
        Returns:
            CrossCameraMovement if match found, None otherwise
        """
        try:
            # Get track for exit event
            exit_track = db.query(Track).filter(
                Track.track_id == exit_event.track_id,
                Track.camera_id == exit_event.camera_id
            ).first()
            
            if not exit_track or not exit_track.reid_embedding:
                logger.debug(f"No Re-ID features for exit track {exit_event.track_id}")
                return None
            
            # Deserialize Re-ID features
            exit_features = pickle.loads(exit_track.reid_embedding)
            
            # Find potential entry events from other cameras
            # Look for entry events within time window (before exit)
            time_window_start = exit_event.timestamp - self.max_time_window
            time_window_end = exit_event.timestamp
            
            # Query entry events from other cameras
            entry_events = db.query(EntryExitLog).filter(
                EntryExitLog.event_type == "entry",
                EntryExitLog.camera_id != exit_event.camera_id,
                EntryExitLog.timestamp >= time_window_start,
                EntryExitLog.timestamp <= time_window_end
            ).order_by(EntryExitLog.timestamp.desc()).all()
            
            if not entry_events:
                logger.debug(f"No entry events found for exit {exit_event.id}")
                return None
            
            # Match against entry events
            best_match = None
            best_similarity = 0.0
            
            for entry_event in entry_events:
                # Get track for entry event
                entry_track = db.query(Track).filter(
                    Track.track_id == entry_event.track_id,
                    Track.camera_id == entry_event.camera_id
                ).first()
                
                if not entry_track or not entry_track.reid_embedding:
                    continue
                
                # Deserialize Re-ID features
                entry_features = pickle.loads(entry_track.reid_embedding)
                
                # Compute similarity
                similarity = self.reid_service.compute_similarity(
                    entry_features, exit_features
                )
                
                # Check if this is a better match
                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_match = entry_event
            
            if best_match:
                # Check if movement already exists (avoid duplicates)
                existing = db.query(CrossCameraMovement).filter(
                    CrossCameraMovement.entry_camera_id == best_match.camera_id,
                    CrossCameraMovement.entry_track_id == best_match.track_id,
                    CrossCameraMovement.exit_camera_id == exit_event.camera_id,
                    CrossCameraMovement.exit_track_id == exit_event.track_id
                ).first()
                
                if existing:
                    logger.debug(f"Cross-camera movement already exists: {existing.id}")
                    return existing
                
                # Create cross-camera movement record
                duration = (exit_event.timestamp - best_match.timestamp).total_seconds()
                match_confidence = self._get_confidence_level(best_similarity)
                
                movement = CrossCameraMovement(
                    entry_camera_id=best_match.camera_id,
                    entry_zone_id=best_match.zone_id,
                    entry_track_id=best_match.track_id,
                    entry_timestamp=best_match.timestamp,
                    exit_camera_id=exit_event.camera_id,
                    exit_zone_id=exit_event.zone_id,
                    exit_track_id=exit_event.track_id,
                    exit_timestamp=exit_event.timestamp,
                    similarity_score=best_similarity,
                    match_confidence=match_confidence,
                    duration_seconds=duration
                )
                
                db.add(movement)
                logger.info(
                    f"Cross-camera match: {best_match.camera_id} (track {best_match.track_id}) -> "
                    f"{exit_event.camera_id} (track {exit_event.track_id}), "
                    f"similarity: {best_similarity:.3f}, duration: {duration:.1f}s"
                )
                
                return movement
            
            return None
            
        except Exception as e:
            logger.error(f"Error matching exit to entry: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_confidence_level(self, similarity: float) -> str:
        """Get confidence level based on similarity score"""
        if similarity >= 0.85:
            return "high"
        elif similarity >= 0.75:
            return "medium"
        else:
            return "low"
    
    def get_movements(
        self,
        db: Session,
        entry_camera_id: Optional[str] = None,
        exit_camera_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[CrossCameraMovement]:
        """
        Query cross-camera movements
        
        Args:
            db: Database session
            entry_camera_id: Filter by entry camera
            exit_camera_id: Filter by exit camera
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results
        
        Returns:
            List of CrossCameraMovement records
        """
        query = db.query(CrossCameraMovement)
        
        if entry_camera_id:
            query = query.filter(CrossCameraMovement.entry_camera_id == entry_camera_id)
        
        if exit_camera_id:
            query = query.filter(CrossCameraMovement.exit_camera_id == exit_camera_id)
        
        if start_time:
            query = query.filter(CrossCameraMovement.entry_timestamp >= start_time)
        
        if end_time:
            query = query.filter(CrossCameraMovement.exit_timestamp <= end_time)
        
        return query.order_by(CrossCameraMovement.entry_timestamp.desc()).limit(limit).all()
    
    def get_movement_statistics(
        self,
        db: Session,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        """
        Get statistics about cross-camera movements
        
        Args:
            db: Database session
            start_time: Filter by start time
            end_time: Filter by end time
        
        Returns:
            Dictionary with statistics
        """
        query = db.query(CrossCameraMovement)
        
        if start_time:
            query = query.filter(CrossCameraMovement.entry_timestamp >= start_time)
        
        if end_time:
            query = query.filter(CrossCameraMovement.exit_timestamp <= end_time)
        
        movements = query.all()
        
        if not movements:
            return {
                "total_movements": 0,
                "unique_camera_pairs": 0,
                "avg_duration_seconds": 0,
                "avg_similarity": 0,
                "high_confidence_count": 0,
                "medium_confidence_count": 0,
                "low_confidence_count": 0
            }
        
        camera_pairs = set()
        durations = []
        similarities = []
        confidence_counts = {"high": 0, "medium": 0, "low": 0}
        
        for movement in movements:
            camera_pairs.add((movement.entry_camera_id, movement.exit_camera_id))
            durations.append(movement.duration_seconds)
            similarities.append(movement.similarity_score)
            confidence_counts[movement.match_confidence] = confidence_counts.get(movement.match_confidence, 0) + 1
        
        return {
            "total_movements": len(movements),
            "unique_camera_pairs": len(camera_pairs),
            "avg_duration_seconds": float(np.mean(durations)) if durations else 0,
            "avg_similarity": float(np.mean(similarities)) if similarities else 0,
            "high_confidence_count": confidence_counts.get("high", 0),
            "medium_confidence_count": confidence_counts.get("medium", 0),
            "low_confidence_count": confidence_counts.get("low", 0)
        }

