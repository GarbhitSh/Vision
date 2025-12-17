"""
Detection service
"""
from ml.detectors import YOLODetector
from typing import List, Dict
import numpy as np
from utils.logger import logger


class DetectionService:
    """Detection service wrapper"""
    
    def __init__(self):
        """Initialize detection service"""
        self.detector = None
        self._initialize()
    
    def _initialize(self):
        """Initialize detector"""
        try:
            self.detector = YOLODetector()
            logger.info("Detection service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize detection service: {e}")
            raise
    
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect people in frame
        
        Args:
            frame: Input frame (BGR format)
        
        Returns:
            List of detections
        """
        if self.detector is None:
            raise RuntimeError("Detector not initialized")
        
        return self.detector.detect(frame)

