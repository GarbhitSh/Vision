"""
Camera capture module
"""
import cv2
import numpy as np
from typing import Optional, Dict
import time


class CameraCapture:
    """Camera capture handler"""
    
    def __init__(self, source, resolution: str = "1920x1080", fps: int = 30):
        """
        Initialize camera capture
        
        Args:
            source: Camera source (device index or RTSP URL)
            resolution: Resolution string like "1920x1080"
            fps: Target FPS
        """
        self.source = source
        self.resolution = resolution
        self.fps = fps
        self.cap = None
        self.width = 1920
        self.height = 1080
        self.last_frame_time = 0
        self.frame_interval = 1.0 / fps if fps > 0 else 0
        
        # Parse resolution
        if resolution:
            try:
                w, h = map(int, resolution.split('x'))
                self.width = w
                self.height = h
            except:
                pass
    
    def initialize(self):
        """Initialize camera connection"""
        try:
            # Try to parse source as integer (USB camera)
            original_source = self.source
            if isinstance(self.source, str) and not self.source.startswith(('http', 'rtsp', 'rtmp')):
                try:
                    self.source = int(self.source)
                except ValueError:
                    # Keep as string if not a number
                    pass
            
            # Try to open camera
            self.cap = cv2.VideoCapture(self.source)
            
            # For DirectShow backend on Windows, try with backend
            if not self.cap.isOpened():
                # Try with DirectShow backend on Windows
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
            
            if not self.cap.isOpened():
                error_msg = f"Failed to open camera source: {original_source}"
                print(error_msg)
                if self.cap:
                    self.cap.release()
                    self.cap = None
                return False
            
            # Set resolution (may not work for all cameras)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Try to read a test frame to verify camera works
            ret, test_frame = self.cap.read()
            if not ret or test_frame is None:
                error_msg = f"Camera opened but cannot read frames from source: {original_source}"
                print(error_msg)
                self.cap.release()
                self.cap = None
                return False
            
            # Verify actual resolution
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            self.width = actual_width if actual_width > 0 else self.width
            self.height = actual_height if actual_height > 0 else self.height
            self.fps = actual_fps if actual_fps > 0 else self.fps
            
            print(f"Camera initialized: {actual_width}x{actual_height} @ {self.fps} FPS")
            return True
        
        except Exception as e:
            error_msg = f"Camera initialization error: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            if self.cap:
                try:
                    self.cap.release()
                except:
                    pass
                self.cap = None
            return False
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        # Throttle frame rate
        current_time = time.time()
        if current_time - self.last_frame_time < self.frame_interval:
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        self.last_frame_time = current_time
        return frame
    
    def is_connected(self) -> bool:
        """Check if camera is connected"""
        return self.cap is not None and self.cap.isOpened()
    
    def get_fps(self) -> float:
        """Get current FPS"""
        return self.fps
    
    def get_camera_info(self) -> Dict:
        """Get camera information"""
        if not self.cap:
            return {}
        
        return {
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "format": "MJPG"  # Default format
        }
    
    def release(self):
        """Release camera resources"""
        if self.cap:
            self.cap.release()
            self.cap = None

