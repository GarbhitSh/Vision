"""
Re-Identification service
"""
from ml.reid_model import ReIDModel
from typing import List, Dict
import numpy as np
from utils.logger import logger


class ReIDService:
    """Re-identification service wrapper"""
    
    def __init__(self):
        """Initialize Re-ID service"""
        self.model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Re-ID model"""
        try:
            self.model = ReIDModel()
            logger.info("Re-ID service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Re-ID service: {e}")
            raise
    
    def extract_features(self, frame: np.ndarray, bbox: List[float]) -> np.ndarray:
        """
        Extract Re-ID features for a person
        
        Args:
            frame: Input frame (BGR format)
            bbox: Bounding box [x, y, w, h]
        
        Returns:
            Feature vector (512-dimensional)
        """
        if self.model is None:
            raise RuntimeError("Re-ID model not initialized")
        
        return self.model.extract_features(frame, bbox)
    
    def compute_similarity(self, feat1: np.ndarray, feat2: np.ndarray) -> float:
        """
        Compute similarity between two feature vectors
        
        Args:
            feat1: First feature vector
            feat2: Second feature vector
        
        Returns:
            Similarity score (0-1)
        """
        if self.model is None:
            raise RuntimeError("Re-ID model not initialized")
        
        return self.model.compute_similarity(feat1, feat2)

