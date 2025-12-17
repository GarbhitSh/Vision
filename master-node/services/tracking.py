"""
Tracking service
"""
from ml.trackers import ByteTracker
from typing import List, Dict
from utils.logger import logger


class TrackingService:
    """Tracking service wrapper"""
    
    def __init__(self):
        """Initialize tracking service"""
        self.trackers = {}  # camera_id -> ByteTracker instance
        logger.info("Tracking service initialized")
    
    def get_tracker(self, camera_id: str) -> ByteTracker:
        """Get or create tracker for camera"""
        if camera_id not in self.trackers:
            self.trackers[camera_id] = ByteTracker()
        return self.trackers[camera_id]
    
    def update(self, camera_id: str, detections: List[Dict]) -> List[Dict]:
        """
        Update tracker with new detections
        
        Args:
            camera_id: Camera identifier
            detections: List of detections
        
        Returns:
            List of tracked objects
        """
        tracker = self.get_tracker(camera_id)
        return tracker.update(detections)
    
    def reset(self, camera_id: str):
        """Reset tracker for camera"""
        if camera_id in self.trackers:
            self.trackers[camera_id].reset()

