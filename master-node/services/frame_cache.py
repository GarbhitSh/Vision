"""
Frame cache for streaming
Stores recent frames for streaming endpoints
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import numpy as np
from collections import deque
import threading

from utils.logger import logger


class FrameCache:
    """Thread-safe frame cache"""
    
    def __init__(self, max_frames: int = 10, ttl_seconds: int = 5):
        """
        Initialize frame cache
        
        Args:
            max_frames: Maximum frames to cache per camera
            ttl_seconds: Time to live for frames in seconds
        """
        self.max_frames = max_frames
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, deque] = {}  # camera_id -> deque of (timestamp, frame, annotations)
        self.lock = threading.Lock()
    
    def add_frame(
        self,
        camera_id: str,
        frame: np.ndarray,
        detections: list,
        tracks: list,
        analytics: dict
    ):
        """Add frame to cache"""
        with self.lock:
            if camera_id not in self.cache:
                self.cache[camera_id] = deque(maxlen=self.max_frames)
            
            self.cache[camera_id].append({
                "timestamp": datetime.utcnow(),
                "frame": frame.copy(),
                "detections": detections,
                "tracks": tracks,
                "analytics": analytics
            })
    
    def get_latest_frame(self, camera_id: str) -> Optional[Dict]:
        """Get latest frame from cache"""
        with self.lock:
            if camera_id not in self.cache or len(self.cache[camera_id]) == 0:
                return None
            
            # Get most recent frame
            latest = self.cache[camera_id][-1]
            
            # Check if still valid
            age = (datetime.utcnow() - latest["timestamp"]).total_seconds()
            if age > self.ttl_seconds:
                return None
            
            return latest
    
    def cleanup_old_frames(self):
        """Remove expired frames"""
        with self.lock:
            now = datetime.utcnow()
            for camera_id in list(self.cache.keys()):
                cache_queue = self.cache[camera_id]
                
                # Remove expired frames
                while len(cache_queue) > 0:
                    oldest = cache_queue[0]
                    age = (now - oldest["timestamp"]).total_seconds()
                    if age > self.ttl_seconds:
                        cache_queue.popleft()
                    else:
                        break
                
                # Remove empty caches
                if len(cache_queue) == 0:
                    del self.cache[camera_id]


# Global frame cache instance
frame_cache = FrameCache()

